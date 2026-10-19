"""Guards for the AWS deploy path (no live AWS required)."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import deploy_k8s_sandbox as k8s_deploy
import deploy_remote as dr

ROOT = Path(__file__).resolve().parents[1]


def _load_script(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_deployer_policy_covers_apply_and_deploy():
    policy = json.loads((ROOT / "terraform/deployer-policy.json").read_text(encoding="utf-8"))
    actions: set[str] = set()
    for stmt in policy["Statement"]:
        raw = stmt["Action"]
        actions.update(raw if isinstance(raw, list) else [raw])
    for needed in (
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:PassRole",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "ssm:SendCommand",
        "ssm:GetCommandInvocation",
        "ssm:DescribeInstanceInformation",
        "ssm:PutParameter",
        "ssm:GetParameter",
        "s3:PutObject",
        "s3:GetObject",
        "s3:CreateBucket",
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
    ):
        assert needed in actions, needed
    blob = json.dumps(policy)
    assert "sre-platform-host-role" in blob
    assert "ec2.amazonaws.com" in blob
    assert "sre-resilienceops-deploy-*" in blob
    assert "ACCOUNT_ID" in blob


def test_terraform_aws_path_knobs():
    tf = (ROOT / "terraform/main.tf").read_text(encoding="utf-8")
    for needle in (
        'output "instance_id"',
        'output "region"',
        'output "deploy_bucket"',
        'output "private_ip"',
        "docker-compose-v2",
        "http_put_response_hop_limit = 2",
        'default     = "t3.medium"',
        "sre-resilienceops-deploy-",
        "/sre/autonomous-agent-audit",
        "/sre/autonomous-agent-incidents",
        "ssm:GetParameter",
        "logs:PutLogEvents",
        "awscli",
    ):
        assert needle in tf, needle
    assert "docker-compose git" not in tf


def test_deploy_remote_uses_s3_and_compose_v2_all_services():
    src = (ROOT / "deploy_remote.py").read_text(encoding="utf-8")
    assert "reports" in dr.INCLUDE_PATHS
    assert "docker compose up --build -d" in src
    assert "docker compose --profile agents" in src
    assert "docker-compose up" not in src
    assert "base64 -d" not in src
    assert "get-parameter" in src
    assert "cloud-init status --wait" in src
    assert "describe_instance_information" in src
    assert "get_command_invocation" in src
    script = dr.build_host_env_script("/resilienceops", "us-east-1")
    assert "get-parameter" in script
    assert "--with-decryption" in script
    assert "supersecret" not in script
    assert "ANTHROPIC_API_KEY" in script
    commands = dr._compose_up_commands(True)
    assert "docker compose up --build -d" in commands
    assert any("--profile agents" in c for c in commands)


def test_ssm_env_keys_match_put_lab_secrets():
    put = _load_script("scripts/put_lab_secrets.py", "put_lab_secrets")
    assert put.KEYS == dr.SSM_ENV_KEYS
    assert "GRAFANA_ADMIN_USER" in put.REQUIRED
    assert "GRAFANA_ADMIN_PASSWORD" in put.REQUIRED


def test_put_lab_secrets_prints_lengths_not_values(monkeypatch, capsys, tmp_path):
    put = _load_script("scripts/put_lab_secrets.py", "put_lab_secrets")
    for key in put.KEYS:
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GRAFANA_ADMIN_USER=admin\nGRAFANA_ADMIN_PASSWORD=supersecret-password\n",
        encoding="utf-8",
    )

    class FakeSSM:
        def put_parameter(self, **kwargs):
            assert kwargs["Type"] == "SecureString"
            return {}

    class FakeBoto3:
        def client(self, name, region_name=None):
            assert name == "ssm"
            return FakeSSM()

    monkeypatch.setitem(__import__("sys").modules, "boto3", FakeBoto3())
    rc = put.main(["--region", "us-east-1", "--env-file", str(env_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "supersecret-password" not in out
    assert "SecureString" in out
    assert f"{len('supersecret-password')} chars" in out


def test_sandbox_script_applies_required_manifests_not_microservices_by_default():
    script = k8s_deploy.sandbox_host_script(apply_microservices=False, skip_copy=False)
    assert "k8s/base/namespace-rbac.yaml" in script
    assert "k8s/agents/agent-sandbox.yaml" in script
    assert "microservices.yaml" not in script
    assert "orchestrator.py" in script
    assert "/app/reports" in script
    assert "PRIVATE_IP" in script
    with_ms = k8s_deploy.sandbox_host_script(apply_microservices=True, skip_copy=True)
    assert "k8s/apps/microservices.yaml" in with_ms


def test_orchestrator_always_resets(monkeypatch):
    import orchestrator as orch

    class Fake:
        def plan_campaign(self, *a, **k):
            return {"llm_model": "x", "strategic_intent": "y"}

        def execute_fault(self, *a, **k):
            return {"scenario": "MEMORY_EXHAUSTION"}

        def inspect_telemetry(self):
            return {"gateway_status": 200, "latency_ms": 5}

        def evaluate_slos(self, curr):
            return None

    monkeypatch.setattr(orch, "faultStrategistAgent", lambda: Fake())
    monkeypatch.setattr(orch, "InfraDisruptorAgent", lambda: Fake())
    monkeypatch.setattr(orch, "NetworkAdversaryAgent", lambda: Fake())
    monkeypatch.setattr(orch, "IncidentMonitor", lambda: Fake())
    monkeypatch.setattr(orch, "DiagnosticAgent", lambda: Fake())
    monkeypatch.setattr(orch, "RemediatorAgent", lambda: Fake())
    monkeypatch.setattr(orch, "PostMortemGenerator", lambda: Fake())
    monkeypatch.setattr(orch.time, "sleep", lambda *_a, **_k: None)
    calls: list[str] = []
    monkeypatch.setattr(
        orch.FaultCatalog,
        "reset_environment",
        staticmethod(lambda: calls.append("reset") or {"ok": True}),
    )
    orch.run_resilience_cycle(1, forced_scenario="MEMORY_EXHAUSTION")
    assert calls == ["reset"]


def test_host_env_script_has_no_secret_literals():
    tree = ast.parse((ROOT / "deploy_remote.py").read_text(encoding="utf-8"))
    func = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_host_env_script"
    )
    joined = ast.get_source_segment((ROOT / "deploy_remote.py").read_text(encoding="utf-8"), func)
    assert joined is not None
    assert "sk-" not in joined
    assert "Bearer " not in joined
    assert "get-parameter" in joined
