"""Apply k3s sandbox manifests on the EC2 host and copy repo code into the pod.

Default AWS path: apps stay in Compose on the host. This script applies
k8s/base/namespace-rbac.yaml (sre-target-apps + Blue RBAC) then
k8s/agents/agent-sandbox.yaml, waits for the sandbox, copies agents/ +
orchestrator.py + reports/, and points API_* URLs at the host private IP.

k8s/apps/microservices.yaml is an *alternate* in-cluster deploy (images
sre-arena/*). It is not applied unless you pass --apply-microservices.

Usage:

    export AWS_REGION=$(terraform -chdir=terraform output -raw region)
    export EC2_INSTANCE_ID=$(terraform -chdir=terraform output -raw instance_id)
    python3 deploy_k8s_sandbox.py --region "$AWS_REGION"
"""

from __future__ import annotations

import argparse

from agents.config import require_ec2_instance_id
from deploy_remote import resolve_region, send_and_wait, wait_for_ssm_online


def sandbox_host_script(*, apply_microservices: bool, skip_copy: bool) -> str:
    micro = ""
    if apply_microservices:
        micro = """
echo '[warn] applying k8s/apps/microservices.yaml (images sre-arena/* must already exist on the node)'
k3s kubectl apply -f /opt/sre-colosseum/k8s/apps/microservices.yaml
"""
    copy = ""
    if not skip_copy:
        copy = r"""
POD=$(k3s kubectl get pod -n sre-agent-sandbox -l agent.role=red-team-fault -o jsonpath='{.items[0].metadata.name}')
echo "sandbox pod=$POD"
k3s kubectl exec -n sre-agent-sandbox "$POD" -- mkdir -p /app/reports /app/agents
k3s kubectl cp /opt/sre-colosseum/agents "sre-agent-sandbox/${POD}:/app/agents"
k3s kubectl cp /opt/sre-colosseum/orchestrator.py "sre-agent-sandbox/${POD}:/app/orchestrator.py"
if [ -d /opt/sre-colosseum/reports ]; then
  k3s kubectl cp /opt/sre-colosseum/reports "sre-agent-sandbox/${POD}:/app/reports"
fi
if [ -f /opt/sre-colosseum/requirements.txt ]; then
  k3s kubectl cp /opt/sre-colosseum/requirements.txt "sre-agent-sandbox/${POD}:/app/requirements.txt"
  k3s kubectl exec -n sre-agent-sandbox "$POD" -- pip install -r /app/requirements.txt python-dotenv || \
    k3s kubectl exec -n sre-agent-sandbox "$POD" -- pip install httpx pydantic python-dotenv kubernetes anthropic prometheus-client
else
  k3s kubectl exec -n sre-agent-sandbox "$POD" -- pip install httpx pydantic python-dotenv kubernetes anthropic prometheus-client
fi
k3s kubectl exec -n sre-agent-sandbox "$POD" -- ls -la /app /app/agents /app/reports
echo "Run a cycle with the host private IP (Compose apps are not in k3s DNS):"
echo "  k3s kubectl exec -it deployment/red-team-sandbox -n sre-agent-sandbox -- python3 orchestrator.py --target-ip $PRIVATE_IP --cycles 1 --scenario MEMORY_EXHAUSTION"
echo "  (pod workingDir is /app; orchestrator.py is copied there)"
"""
    return f"""
set -euo pipefail
test -f /opt/sre-colosseum/k8s/base/namespace-rbac.yaml
test -f /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml
k3s kubectl apply -f /opt/sre-colosseum/k8s/base/namespace-rbac.yaml
k3s kubectl apply -f /opt/sre-colosseum/k8s/agents/agent-sandbox.yaml
{micro}
TOKEN=$(curl -sS -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')
PRIVATE_IP=$(curl -sS -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4)
echo "host private_ip=$PRIVATE_IP"
k3s kubectl set env deployment/red-team-sandbox -n sre-agent-sandbox \
  API_GATEWAY_URL="http://$PRIVATE_IP:8000" \
  ORDER_SERVICE_URL="http://$PRIVATE_IP:8001" \
  PAYMENT_SERVICE_URL="http://$PRIVATE_IP:8002" \
  PROMETHEUS_URL="http://$PRIVATE_IP:9090" \
  --overwrite
# Compose publishes Prometheus on 127.0.0.1:9090. Also bind the private IP
# so this pod can query http://$PRIVATE_IP:9090. Never 0.0.0.0; ingress_sg
# does not open 9090 (same-host k3s is local delivery).
if [ -f /opt/sre-colosseum/docker-compose.prom-lan.yml ]; then
  case "$PRIVATE_IP" in
    ''|0.0.0.0|127.*) echo "[warn] skipping Prometheus LAN bind for '$PRIVATE_IP'" ;;
    *)
      if grep -q '^PROMETHEUS_BIND=' /opt/sre-colosseum/.env 2>/dev/null; then
        sed -i '/^PROMETHEUS_BIND=/d' /opt/sre-colosseum/.env
      fi
      printf 'PROMETHEUS_BIND=%s\n' "$PRIVATE_IP" >> /opt/sre-colosseum/.env
      if grep -q '^COMPOSE_FILE=' /opt/sre-colosseum/.env 2>/dev/null; then
        sed -i '/^COMPOSE_FILE=/d' /opt/sre-colosseum/.env
      fi
      printf 'COMPOSE_FILE=docker-compose.yml:docker-compose.prom-lan.yml\n' >> /opt/sre-colosseum/.env
      (cd /opt/sre-colosseum && docker compose up -d prometheus)
      echo "[ok] Prometheus also published on $PRIVATE_IP:9090 for k3s"
      ;;
  esac
fi
if [ -f /opt/sre-colosseum/.env ] && grep -q '^ANTHROPIC_API_KEY=.\\+' /opt/sre-colosseum/.env; then
  umask 077
  grep '^ANTHROPIC_API_KEY=' /opt/sre-colosseum/.env > /tmp/sandbox-anthropic.env
  k3s kubectl create secret generic sandbox-anthropic -n sre-agent-sandbox \
    --from-env-file=/tmp/sandbox-anthropic.env --dry-run=client -o yaml | k3s kubectl apply -f -
  rm -f /tmp/sandbox-anthropic.env
  k3s kubectl set env deployment/red-team-sandbox -n sre-agent-sandbox --from=secret/sandbox-anthropic --overwrite
else
  echo '[warn] ANTHROPIC_API_KEY not present in host .env; Claude calls from the sandbox will fail'
fi
k3s kubectl rollout status deployment/red-team-sandbox -n sre-agent-sandbox --timeout=180s
k3s kubectl wait --for=condition=Ready pod -l agent.role=red-team-fault -n sre-agent-sandbox --timeout=180s
{copy}
k3s kubectl get pods,roles,rolebindings,networkpolicies -n sre-agent-sandbox
k3s kubectl get ns sre-target-apps
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default=None)
    parser.add_argument(
        "--apply-microservices",
        action="store_true",
        help="Also apply k8s/apps/microservices.yaml (requires pre-built sre-arena/* images). Default AWS lab uses Compose.",
    )
    parser.add_argument("--skip-copy", action="store_true", help="Apply manifests only; do not kubectl cp repo code")
    parser.add_argument("--skip-wait-ssm", action="store_true")
    args = parser.parse_args(argv)

    region = resolve_region(args.region)
    instance_id = require_ec2_instance_id()

    import boto3

    ssm = boto3.client("ssm", region_name=region)
    if not args.skip_wait_ssm:
        wait_for_ssm_online(ssm, instance_id)
    send_and_wait(
        ssm,
        instance_id,
        [sandbox_host_script(apply_microservices=args.apply_microservices, skip_copy=args.skip_copy)],
        comment="resilienceops-k8s-sandbox",
        timeout_s=1200,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
