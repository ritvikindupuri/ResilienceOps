"""Copy agents/, orchestrator.py, and reports/ into the running k3s sandbox pod.

Prefer `python3 deploy_k8s_sandbox.py` (apply + wait + copy). This script is
the copy-only follow-up if the pod was recreated.

ANTHROPIC_API_KEY is read from /opt/sre-colosseum/.env on the host (written by
deploy_remote.py from Parameter Store). It is not taken from the SSM shell env
and is not printed.
"""

from __future__ import annotations

import argparse

from agents.config import require_ec2_instance_id
from deploy_k8s_sandbox import sandbox_host_script
from deploy_remote import resolve_region, send_and_wait, wait_for_ssm_online


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=None)
    parser.add_argument("--skip-wait-ssm", action="store_true")
    args = parser.parse_args(argv)

    region = resolve_region(args.region)
    instance_id = require_ec2_instance_id()

    import boto3

    ssm = boto3.client("ssm", region_name=region)
    if not args.skip_wait_ssm:
        wait_for_ssm_online(ssm, instance_id)
    # Re-apply env + copy after a pod restart. Manifests are already on the host.
    send_and_wait(
        ssm,
        instance_id,
        [sandbox_host_script(apply_microservices=False, skip_copy=False)],
        comment="resilienceops-sandbox-copy",
        timeout_s=1200,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
