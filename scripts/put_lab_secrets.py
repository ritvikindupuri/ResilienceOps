#!/usr/bin/env python3
"""Copy local .env values into SSM Parameter Store as SecureString.

Values travel operator-laptop → Parameter Store over the AWS API. They are
never placed in an SSM SendCommand document (that history is visible).
deploy_remote.py later has the instance read them with its instance role
and write /opt/sre-colosseum/.env on the host.

Usage (from the repo root, after terraform apply):

    export AWS_REGION=$(terraform -chdir=terraform output -raw region)
    python3 scripts/put_lab_secrets.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Names written to /resilienceops/<NAME>. Keep in sync with deploy_remote.SSM_ENV_KEYS.
KEYS = [
    "GRAFANA_ADMIN_USER",
    "GRAFANA_ADMIN_PASSWORD",
    "ANTHROPIC_API_KEY",
    "GROK_WEBHOOK_URL",
    "GROK_WEBHOOK_KEY",
    "GROK_WEBHOOK_AUTH_HEADER",
    "GROK_WEBHOOK_AUTH_SCHEME",
    "POSTGRES_PASSWORD",
    "GITHUB_TOKEN",
    "GITHUB_REPOSITORY",
]

REQUIRED = ("GRAFANA_ADMIN_USER", "GRAFANA_ADMIN_PASSWORD")
# SSM PutParameter rejects empty Value. Host script writes KEY= for this sentinel
# so GROK_WEBHOOK_AUTH_SCHEME= (raw key, no Bearer) survives the AWS path.
EMPTY_SENTINEL = "__EMPTY__"


def _load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip("'").strip('"')
    return values


def parameter_name(prefix: str, key: str) -> str:
    return f"{prefix.rstrip('/')}/{key}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1")
    parser.add_argument("--prefix", default=os.getenv("SSM_PARAM_PREFIX", "/resilienceops"))
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args(argv)

    file_vals = _load_dotenv(Path(args.env_file))
    missing_required = [k for k in REQUIRED if not (os.getenv(k) or file_vals.get(k))]
    if missing_required:
        print(
            "missing required values (set in .env or the environment): "
            + ", ".join(missing_required),
            file=sys.stderr,
        )
        return 1

    import boto3

    ssm = boto3.client("ssm", region_name=args.region)
    written = 0
    skipped = 0
    for key in KEYS:
        present_in_env = key in os.environ
        present_in_file = key in file_vals
        if present_in_env:
            value = os.environ.get(key, "")
        elif present_in_file:
            value = file_vals.get(key, "")
        else:
            skipped += 1
            print(f"skip {key} (unset)")
            continue
        stored = EMPTY_SENTINEL if value == "" else value
        name = parameter_name(args.prefix, key)
        ssm.put_parameter(
            Name=name,
            Value=stored,
            Type="SecureString",
            Overwrite=True,
            Tier="Standard",
        )
        written += 1
        shown = "empty" if stored == EMPTY_SENTINEL else f"{len(value)} chars"
        print(f"put {name} (SecureString, {shown})")
    print(f"wrote {written} parameter(s), skipped {skipped} unset; region={args.region}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
