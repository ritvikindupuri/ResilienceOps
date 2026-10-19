"""Build a deploy archive from the working tree and push it via SSM.

Secrets are never bundled. Provide ANTHROPIC_API_KEY, GRAFANA_ADMIN_USER,
GRAFANA_ADMIN_PASSWORD, POSTGRES_PASSWORD, and GROK_WEBHOOK_* on the host
via the environment, SSM Parameter Store, or Secrets Manager.
"""

import base64
import io
import os
import zipfile
from pathlib import Path

from agents.config import AWS_REGION, require_ec2_instance_id

REPO_ROOT = Path(__file__).resolve().parent

# Same compose-oriented payload the host expects, without secrets.
INCLUDE_PATHS = [
    "services",
    "dashboards",
    "traffic-generator",
    "docker-compose.yml",
    "agents",
    "orchestrator.py",
    "requirements.txt",
    ".env.example",
    "k8s",
    "Dockerfile.agent-sandbox",
]

EXCLUDE_DIR_NAMES = {".git", "__pycache__", ".terraform", "logs"}
EXCLUDE_FILE_NAMES = {"deploy_payload.zip"}
EXCLUDE_SUFFIXES = {".pyc", ".tfstate", ".tfstate.backup"}


def _is_secret_env_file(name: str) -> bool:
    return name.endswith(".env") and name != ".env.example"


def should_exclude(path: Path) -> bool:
    rel_parts = set(path.relative_to(REPO_ROOT).parts)
    if rel_parts & EXCLUDE_DIR_NAMES:
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    if _is_secret_env_file(path.name):
        return True
    if path.name.endswith(".zip") and "payload" in path.name.lower():
        return True
    return False


def build_deploy_archive(root: Path = REPO_ROOT) -> bytes:
    """Create a zip from the tree. Never includes .env or other secret env files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in INCLUDE_PATHS:
            source = root / rel
            if not source.exists():
                continue
            if source.is_file():
                if not should_exclude(source):
                    zf.write(source, rel)
                continue
            for dirpath, dirnames, filenames in os.walk(source):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
                for name in filenames:
                    full = Path(dirpath) / name
                    if should_exclude(full):
                        continue
                    zf.write(full, full.relative_to(root).as_posix())
    data = buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as verify:
        leaked = [n for n in verify.namelist() if _is_secret_env_file(Path(n).name)]
        if leaked:
            raise RuntimeError(f"Refusing to deploy: archive contains secret env files: {leaked}")
    return data


def main() -> None:
    instance_id = require_ec2_instance_id()
    payload = build_deploy_archive()
    b64_payload = base64.b64encode(payload).decode("ascii")

    import boto3

    ssm = boto3.client("ssm", region_name=AWS_REGION)
    commands = [
        "mkdir -p /opt/sre-colosseum",
        "cd /opt/sre-colosseum",
        f"cat << 'EOF' | base64 -d > deploy_payload.zip\n{b64_payload}\nEOF",
        "apt-get install -y unzip",
        "unzip -o deploy_payload.zip",
        # Secrets stay on the host / SSM / Secrets Manager — never in the zip.
        "test -n \"$ANTHROPIC_API_KEY\" || echo '[warn] ANTHROPIC_API_KEY is not set on the host'",
        "test -n \"$GRAFANA_ADMIN_USER\" && test -n \"$GRAFANA_ADMIN_PASSWORD\" || "
        "echo '[warn] Grafana admin credentials are not set on the host'",
        "docker-compose up --build -d grafana prometheus api-gw order-service payment-service traffic-generator",
        "docker ps",
    ]

    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": commands},
    )
    cmd_id = resp["Command"]["CommandId"]
    print("Dispatched SSM deployment command:", cmd_id)


if __name__ == "__main__":
    main()
