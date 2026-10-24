"""Keep README, .env.example, and referenced scripts aligned with the code."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _python_getenv_names() -> set[str]:
    names: set[str] = set()
    skip_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    for path in ROOT.rglob("*.py"):
        if any(part in skip_dirs for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"_env_int", "_env_float"}:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    names.add(node.args[0].value)
                continue
            is_getenv = False
            if isinstance(func, ast.Attribute) and func.attr == "getenv":
                is_getenv = True
            if not is_getenv:
                continue
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                names.add(node.args[0].value)
    return names


def _env_example_keys() -> set[str]:
    keys: set[str] = set()
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        body = stripped[2:].strip() if stripped.startswith("#") else stripped
        if "=" in body and re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", body):
            keys.add(body.split("=", 1)[0].strip())
    return keys


def _compose_interpolation_names() -> set[str]:
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    return set(re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)", text))


def test_env_example_covers_python_getenv_names():
    documented = _env_example_keys()
    missing = sorted(_python_getenv_names() - documented)
    assert missing == [], f"add these to .env.example: {missing}"


def test_env_example_covers_compose_interpolation_names():
    documented = _env_example_keys()
    missing = sorted(_compose_interpolation_names() - documented)
    assert missing == [], f"compose interpolates undeclared env vars: {missing}"


def test_readme_documents_env_example_keys():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = sorted(name for name in _env_example_keys() if f"`{name}`" not in readme)
    assert missing == [], f"README should mention these env vars: {missing}"


def test_readme_referenced_scripts_exist():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = [
        "scripts/send_test_alert.py",
        "scripts/render_architecture.sh",
        "scripts/build_architecture.py",
        "orchestrator.py",
        "deploy_remote.py",
        "deploy_k8s_sandbox.py",
        "copy_code_to_sandbox.py",
        "scripts/put_lab_secrets.py",
        "terraform/deployer-policy.json",
        "teardown.sh",
        "teardown.ps1",
        ".env.example",
        "docker-compose.prom-lan.yml",
        "dashboards/prometheus.yml",
        "dashboards/alerts.yml",
        "dashboards/alertmanager.yml",
        "docs/architecture.svg",
        "docs/architecture.mmd",
        "docs/ACCURACY.md",
        "docs/images/infraattack_platform_architecture.png",
        "docs/images/sample-incident-issue-1.png",
        "docs/images/sample-incident-issue-2.png",
        "docs/images/sample-incident-issue-3.png",
        "docs/images/sample-incident-issue-5-1.png",
        "docs/images/sample-incident-issue-5-2.png",
        "docs/images/sample-incident-issue-5-3.png",
        "examples/e2e_test_alert.json",
        "examples/live_run_issue5_timeline.md",
        "examples/live_run_issue5_bridge.log",
        "docs/ResilienceOps_Technical_Documentation.pdf",
        "scripts/generate_example_post_mortem.py",
        "reports/example_incident_memory_exhaustion.md",
        "remediation/remediate.py",
        "remediation/e2e_local.py",
        ".github/workflows/remediation-approve.yml",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), rel
        if rel.startswith("scripts/") or rel.endswith((".sh", ".py", ".svg", ".mmd", ".png", ".yml")):
            assert rel in readme or rel.split("/")[-1] in readme, f"README should mention {rel}"


def test_readme_flow_names_match_code_stages():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in (
        "**Fault injection**",
        "**Detection**",
        "**Alert**",
        "**Enrichment**",
        "**Diagnosis**",
        "**Issue**",
        "**Handoff**",
        "**Proposal**",
        "**Approval**",
        "**Fix**",
        "**Resolution**",
    ):
        assert heading in readme, heading
    for scenario in (
        "MEMORY_EXHAUSTION",
        "REDIS_CONNECTION_STARVATION",
        "CPU_SATURATION",
        "NETWORK_LATENCY",
        "PACKET_LOSS",
    ):
        assert f"--scenario {scenario}" in readme or scenario in readme, scenario


def test_readme_sample_post_mortem_is_current_generator():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sample = (ROOT / "reports" / "example_incident_memory_exhaustion.md").read_text(encoding="utf-8")
    assert "AWS (optional)" in readme
    assert "[Quick start (local)](#quick-start-local)" in readme
    assert "[AWS (optional)](#aws-optional)" in readme
    assert "reports/example_incident_memory_exhaustion.md" in readme
    assert "pre-fix historical" in readme
    assert "# Incident Post-Mortem Report: UNKNOWN_FAULT" not in readme
    assert "Example report" in sample
    assert "Incident Post-Mortem Report: MEMORY_EXHAUSTION" in sample
    assert "issue #5" in readme or "issues/5" in readme
    assert "RedisConnectionSaturation" in readme
    assert "forward FAILED after" in readme
    assert "POST /fault/reset" in readme
    assert "12.1 s" in readme
    assert "examples/live_run_issue5_timeline.md" in readme
    assert "examples/live_run_issue5_bridge.log" in readme
    assert "Blue checks health on all 3 and resets order-service and payment-service" in readme
    svg = (ROOT / "docs" / "architecture.svg").read_text(encoding="utf-8")
    assert "Your Grok bot" not in svg
    assert "Your Grok bot" not in readme
    assert "optional AWS" in svg
    assert "watches and resets" in svg
    assert "health on all 3" not in svg
    assert "reset order + payment" not in svg
    assert "faults order" in svg
    assert "→ OS" not in svg
    assert "faults OS+PS" not in svg
    assert "/sre/autonomous-agent-audit" not in svg
    assert "Grok Bot (external)" not in svg
    assert "AI Incident Diagnosis" in svg
    assert "queries Prometheus" in svg
    assert "reads metrics" in svg
    assert "PromQL · jsonl" not in svg
    assert "creates the infra" in svg
    assert "Secrets script" not in svg
    assert "Deploy script" not in svg
    assert "stores the app bundle" not in svg
    assert "runs deploy commands" not in svg
    assert "holds secrets" not in svg
    assert "agents in one sandbox pod" in svg
    assert "optional: agents in a sandbox pod" not in svg
    assert "EC2 host · public subnet 10.0.1.0/24 · VPC 10.0.0.0/16" in svg
    assert "1–6 diagnosis path" in svg
    assert "Grey edges are supporting" in readme
    assert "incident-bridge queries Prometheus" in readme
    assert "allowed_cidr" not in svg
    assert "/metrics" not in svg
    assert "reads Prom" not in svg
    for filename in (
        "put_lab_secrets.py",
        "deploy_remote.py",
        "orchestrator.py",
        "jsonl",
        "FAULT_HOLD_SECONDS",
        "send_command",
        "CloudWatch log groups",
        "webhook in",
        "app_workloads",
        "data_persistence",
    ):
        assert filename not in svg, filename
    assert "Grafana and API ports from your IP" in svg
    assert "Stack (Docker Compose)" in svg
    assert "Docker Compose on this host" not in svg
    assert "k3s sandbox (optional)" in svg
    assert "Runs the agents in isolated pods" not in svg
    assert "k3s (optional)" not in svg
    assert "read-only" not in svg.lower()
    assert "Owner ping" in svg
    assert "1–6 diagnosis path" in svg
    assert "7–10 remediator path" in svg
    assert "Incident Remediation" in svg
    assert "AI Incident Diagnosis" in svg
    assert "Actions" in svg
    assert "host poller" in svg
    assert "arrow-rem" in svg
    assert "How ResilienceOps plus the diagnosis and remediator bots work" in svg
    assert "FAULT_HOLD_SECONDS" in readme
    assert "PROMETHEUS_BIND" in readme
    assert "COMPOSE_FILE" in readme
    assert "create-policy" in readme
    assert "attach-user-policy" in readme
    assert "attach-role-policy" in readme
    assert "detach-user-policy" in readme
    assert "delete-policy" in readme
    assert "put-user-policy" not in readme
    assert "delete-user-policy" not in readme
    assert "cd terraform" not in readme
    assert "terraform -chdir=terraform" in readme
    assert "169.254.169.254" in readme
    assert "session-manager-plugin" in readme
    assert "workingDir" in readme
    assert "sre-target-apps" in readme
    assert "--apply-microservices" in readme
    assert "ResilienceOpsDeployer" in readme
    assert "terraform/deployer-policy.json" in readme
    assert "put_lab_secrets.py" in readme
    assert "deploy_k8s_sandbox.py" in readme
    assert "--profile agents" in readme
    assert "export AWS_REGION" in readme
    assert "output -raw instance_id" in readme
    assert "docker compose up --build -d" in readme
    assert "FaultCatalog.reset_environment" in readme or "finally" in readme
    assert "Grafana and API ports from your IP" in svg
    assert "CloudWatch log groups" in readme
    assert "app_workloads 10.0.10.0/24" in readme
    assert "data_persistence 10.0.20.0/24" in readme
    assert "webhook in" in readme
    assert "send_command" in readme
    assert "logging.getLogger(\"httpx\").setLevel(logging.WARNING)" in (
        ROOT / "services" / "incident-bridge" / "app.py"
    ).read_text(encoding="utf-8")
    assert "K8sToolKit.k8s_available" in readme
    assert "bounces the container" not in readme
    assert "MTTD: 2.14s" not in readme
    assert "MTTR: 3.42s" not in readme


def test_live_run_artifacts_redact_webhook_url():
    uuidish = re.compile(r"automations/webhook/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-")
    for rel in (
        "examples/live_run_issue5_timeline.md",
        "examples/live_run_issue5_bridge.log",
        "README.md",
        "docs/ACCURACY.md",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert uuidish.search(text) is None, f"webhook UUID leaked in {rel}"
    timeline = (ROOT / "examples" / "live_run_issue5_timeline.md").read_text(encoding="utf-8")
    log = (ROOT / "examples" / "live_run_issue5_bridge.log").read_text(encoding="utf-8")
    assert "12.1 s" in timeline
    assert "21:51:11.134" in timeline
    assert "21:52:06" in timeline
    assert "<redacted>" in log
    assert "forwarded 1 alert(s) status=firing" in log
    assert "ConnectTimeout" in log


def _load_arch():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_architecture", ROOT / "scripts" / "build_architecture.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_architecture_geometry_has_no_overlaps():
    hits = _load_arch().check_geometry()
    assert hits == [], "architecture geometry violations:\n  " + "\n  ".join(hits[:20])


def test_geometry_flags_line_through_any_text():
    """A shaft through a caption is a hit even when that caption is owned."""
    mod = _load_arch()
    scene = mod.Scene(400, 400)
    scene.text(200, 200, "resets", 24, bold=False, anchor="middle", name="cap:Blue Team")
    scene.add_seg(200, 160, 200, 240, "blue-svc:1", frozenset({"cap:Blue Team"}))
    hits = scene.check()
    assert any("through text cap:Blue Team" in item for item in hits), hits


def test_architecture_icon_pngs_have_transparent_corners():
    mod = _load_arch()
    hits = mod.check_icon_png_corners()
    assert hits == [], "icon PNG corners must be transparent:\n  " + "\n  ".join(hits)


def test_architecture_png_is_nontrivial():
    import struct

    data = (ROOT / "docs/images/infraattack_platform_architecture.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 80_000
    width, height = struct.unpack(">II", data[16:24])
    # Native SVG is 1480×1380; render_architecture.sh writes 2×.
    assert width in {1480, 2960}, width
    assert height in {1180, 1340, 1380, 2360, 2680, 2760}, height


_ACCURACY_FILE_LINE = re.compile(
    r"`((?:[\w./-]+/)?[\w.-]+\.(?:py|yml|yaml|tf|json|md|txt|sh|ps1)):(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)`"
)


def _resolve_accuracy_file(cited: str) -> Path | None:
    direct = ROOT / cited
    if direct.is_file():
        return direct
    matches = [
        path
        for path in ROOT.rglob(Path(cited).name)
        if path.is_file() and ".git" not in path.parts
    ]
    suffixed = [path for path in matches if str(path).replace("\\", "/").endswith(cited)]
    if len(suffixed) == 1:
        return suffixed[0]
    if cited.count("/") == 0:
        named = [path for path in matches if path.name == cited]
        if len(named) == 1:
            return named[0]
    return None


def test_accuracy_file_line_refs_exist():
    """Every `file:line` citation in ACCURACY.md must still land in that file."""
    text = (ROOT / "docs" / "ACCURACY.md").read_text(encoding="utf-8")
    missing: list[str] = []
    for match in _ACCURACY_FILE_LINE.finditer(text):
        cited, spec = match.group(1), match.group(2)
        path = _resolve_accuracy_file(cited)
        if path is None:
            missing.append(f"{cited}:{spec} (file not found)")
            continue
        line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        for part in spec.split(","):
            if "-" in part:
                start_s, end_s = part.split("-", 1)
                lines = [int(start_s), int(end_s)]
            else:
                lines = [int(part)]
            for line in lines:
                if line < 1 or line > line_count:
                    missing.append(
                        f"{cited}:{line} ({path.relative_to(ROOT)} has {line_count} lines)"
                    )
    assert missing == [], "stale ACCURACY.md file:line refs:\n  " + "\n  ".join(missing)


def test_accuracy_readme_section_refs():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    accuracy = (ROOT / "docs" / "ACCURACY.md").read_text(encoding="utf-8")
    assert "README step 10" not in accuracy
    for heading in (
        "## Prerequisites",
        "### Two AWS identities",
        "### Optional k3s sandbox",
        "### No proposal appeared",
        "## Troubleshooting",
    ):
        assert heading in readme, heading
