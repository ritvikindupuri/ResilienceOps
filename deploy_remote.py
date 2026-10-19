"""Build a deploy archive and push it to the EC2 host via S3 + SSM.

The zip is uploaded to the Terraform deploy bucket so SSM SendCommand stays
under the 100 KB document limit. Secrets never go in the zip or in SendCommand
history: the instance reads SSM Parameter Store SecureStrings with its instance
role and writes /opt/sre-colosseum/.env.

Usage (from the repo root, after terraform apply):

    export AWS_REGION=$(terraform -chdir=terraform output -raw region)
    export AWS_DEFAULT_REGION="$AWS_REGION"
    export EC2_INSTANCE_ID=$(terraform -chdir=terraform output -raw instance_id)
    export DEPLOY_BUCKET=$(terraform -chdir=terraform output -raw deploy_bucket)
    python3 scripts/put_lab_secrets.py --region "$AWS_REGION"
    python3 deploy_remote.py --region "$AWS_REGION"
    python3 deploy_remote.py --region "$AWS_REGION" --profile agents
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
import zipfile
from pathlib import Path

from agents.config import require_ec2_instance_id

REPO_ROOT = Path(__file__).resolve().parent

# Same compose-oriented payload the host expects, without secrets.
# reports/ is required by Dockerfile.agent-sandbox COPY reports/.
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
    "reports",
    "deploy_k8s_sandbox.py",
    "copy_code_to_sandbox.py",
]

EXCLUDE_DIR_NAMES = {".git", "__pycache__", ".terraform", "logs"}
EXCLUDE_FILE_NAMES = {"deploy_payload.zip"}
EXCLUDE_SUFFIXES = {".pyc", ".tfstate", ".tfstate.backup"}

# Keep in sync with scripts/put_lab_secrets.py KEYS.
SSM_ENV_KEYS = [
    "GRAFANA_ADMIN_USER",
    "GRAFANA_ADMIN_PASSWORD",
    "ANTHROPIC_API_KEY",
    "GROK_WEBHOOK_URL",
    "GROK_WEBHOOK_KEY",
    "GROK_WEBHOOK_AUTH_HEADER",
    "GROK_WEBHOOK_AUTH_SCHEME",
    "POSTGRES_PASSWORD",
]
REQUIRED_HOST_ENV = ("GRAFANA_ADMIN_USER", "GRAFANA_ADMIN_PASSWORD")
DEFAULT_SSM_PREFIX = "/resilienceops"


def resolve_region(explicit: str | None = None) -> str:
    return (
        (explicit or "").strip()
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )


def resolve_bucket(explicit: str | None = None) -> str:
    value = (explicit or os.getenv("DEPLOY_BUCKET") or "").strip()
    if not value:
        raise RuntimeError(
            "DEPLOY_BUCKET is not set. Export the Terraform output before deploy, "
            "for example: export DEPLOY_BUCKET=$(terraform -chdir=terraform output -raw deploy_bucket)"
        )
    return value


def resolve_ssm_prefix(explicit: str | None = None) -> str:
    return (explicit or os.getenv("SSM_PARAM_PREFIX") or DEFAULT_SSM_PREFIX).rstrip("/")


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


def wait_for_ssm_online(ssm, instance_id: str, timeout_s: int = 720) -> None:
    """Block until the SSM agent reports PingStatus=Online (user_data takes minutes)."""
    deadline = time.time() + timeout_s
    last_status = "unknown"
    print(f"Waiting for SSM agent Online on {instance_id} (timeout {timeout_s}s)...")
    while time.time() < deadline:
        resp = ssm.describe_instance_information(
            Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
        )
        infos = resp.get("InstanceInformationList") or []
        if infos:
            last_status = infos[0].get("PingStatus") or "unknown"
            if last_status == "Online":
                print(f"SSM agent Online on {instance_id}")
                return
        time.sleep(10)
    raise SystemExit(
        f"SSM agent not Online on {instance_id} within {timeout_s}s (last status={last_status}). "
        "cloud-init (apt, docker, k3s) may still be running; retry after a few minutes."
    )


def send_and_wait(
    ssm,
    instance_id: str,
    commands: list[str],
    *,
    timeout_s: int = 1800,
    comment: str = "resilienceops-deploy",
) -> dict:
    """Send AWS-RunShellScript and fail non-zero unless Status=Success."""
    resp = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Comment=comment[:100],
        Parameters={"commands": commands},
    )
    cmd_id = resp["Command"]["CommandId"]
    print(f"SSM CommandId={cmd_id} comment={comment}")
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        try:
            last = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
        except ssm.exceptions.InvocationDoesNotExist:
            time.sleep(3)
            continue
        status = last.get("Status")
        if status in {"Pending", "InProgress", "Delayed"}:
            time.sleep(5)
            continue
        stdout = last.get("StandardOutputContent") or ""
        stderr = last.get("StandardErrorContent") or ""
        if stdout:
            print(stdout, end="" if stdout.endswith("\n") else "\n")
        if stderr:
            print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
        print(f"SSM command {cmd_id} status={status}")
        if status != "Success":
            raise SystemExit(f"SSM command {cmd_id} ended with status={status}")
        return last
    raise SystemExit(f"SSM command {cmd_id} did not finish within {timeout_s}s")


def build_host_env_script(prefix: str, region: str) -> str:
    """Shell that writes /opt/sre-colosseum/.env from Parameter Store.

    Parameter *names* appear in SendCommand history. Values are read on the
    host via the instance role and are never interpolated into this script.
    """
    keys = " ".join(SSM_ENV_KEYS)
    required = " ".join(REQUIRED_HOST_ENV)
    return f"""
PREFIX='{prefix}'
REGION='{region}'
ENV_FILE=/opt/sre-colosseum/.env
mkdir -p /opt/sre-colosseum
umask 077
: > "$ENV_FILE"
for KEY in {keys}; do
  NAME="${{PREFIX}}/${{KEY}}"
  VAL=$(aws ssm get-parameter --name "$NAME" --with-decryption --region "$REGION" --query Parameter.Value --output text 2>/dev/null || true)
  if [ -n "$VAL" ] && [ "$VAL" != "None" ]; then
    printf '%s=%s\\n' "$KEY" "$VAL" >> "$ENV_FILE"
  fi
done
for KEY in {required}; do
  if ! grep -q "^${{KEY}}=.\\+" "$ENV_FILE"; then
    echo "[error] $KEY missing from Parameter Store ($PREFIX/$KEY). Run: python3 scripts/put_lab_secrets.py --region $REGION" >&2
    exit 1
  fi
done
if grep -q '^ANTHROPIC_API_KEY=.\\+' "$ENV_FILE"; then
  echo '[ok] ANTHROPIC_API_KEY is set in host .env'
else
  echo '[warn] ANTHROPIC_API_KEY is not set in host .env (Red/Blue Claude calls will fail)'
fi
if grep -q '^GROK_WEBHOOK_URL=.\\+' "$ENV_FILE"; then
  echo '[ok] GROK_WEBHOOK_URL is set in host .env'
else
  echo '[warn] GROK_WEBHOOK_URL is not set in host .env (incident-bridge will drop alerts)'
fi
chmod 600 "$ENV_FILE"
"""


def _upload_payload(s3, bucket: str, instance_id: str, payload: bytes) -> tuple[str, str]:
    key = f"deploy/{instance_id}/{int(time.time())}/payload.zip"
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=payload,
        ServerSideEncryption="AES256",
        ContentType="application/zip",
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )
    print(f"Uploaded deploy archive s3://{bucket}/{key} ({len(payload)} bytes)")
    return key, url


def _compose_up_commands(with_agents: bool) -> list[str]:
    commands = [
        "cd /opt/sre-colosseum",
        "docker compose version",
        "docker compose up --build -d",
    ]
    if with_agents:
        commands.append("docker compose --profile agents up --build -d")
    commands.append("docker compose ps")
    return commands


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=None, help="AWS region (default AWS_REGION / AWS_DEFAULT_REGION / us-east-1)")
    parser.add_argument("--bucket", default=None, help="Deploy bucket (default DEPLOY_BUCKET)")
    parser.add_argument("--ssm-prefix", default=None, help="Parameter Store prefix (default SSM_PARAM_PREFIX / /resilienceops)")
    parser.add_argument(
        "--profile",
        choices=["agents"],
        default=None,
        help="Also start the opt-in agent-sandbox Compose service (needs ANTHROPIC_API_KEY in Parameter Store)",
    )
    parser.add_argument("--skip-wait-ssm", action="store_true", help="Do not wait for SSM Online (debug only)")
    args = parser.parse_args(argv)

    region = resolve_region(args.region)
    instance_id = require_ec2_instance_id()
    bucket = resolve_bucket(args.bucket)
    prefix = resolve_ssm_prefix(args.ssm_prefix)
    with_agents = args.profile == "agents"

    payload = build_deploy_archive()

    import boto3

    ssm = boto3.client("ssm", region_name=region)
    s3 = boto3.client("s3", region_name=region)

    if not args.skip_wait_ssm:
        wait_for_ssm_online(ssm, instance_id)

    _key, url = _upload_payload(s3, bucket, instance_id, payload)

    commands = [
        "set -euo pipefail",
        "export AWS_DEFAULT_REGION=" + region,
        "cloud-init status --wait || true",
        "mkdir -p /opt/sre-colosseum",
        "cd /opt/sre-colosseum",
        build_host_env_script(prefix, region).strip(),
        # Presigned URL is fetched on the host; the zip has no secrets.
        f"curl -fsSL -o /opt/sre-colosseum/deploy_payload.zip '{url}'",
        "command -v unzip >/dev/null || apt-get install -y unzip",
        "unzip -o /opt/sre-colosseum/deploy_payload.zip -d /opt/sre-colosseum",
        "test -d /opt/sre-colosseum/reports || mkdir -p /opt/sre-colosseum/reports",
        *_compose_up_commands(with_agents),
    ]
    send_and_wait(
        ssm,
        instance_id,
        commands,
        comment="resilienceops-compose-deploy",
    )
    print("Deploy finished. Grafana vars came from Parameter Store; secrets were not in SendCommand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
