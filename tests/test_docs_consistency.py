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
        "orchestrator.py",
        "deploy_remote.py",
        "teardown.sh",
        "teardown.ps1",
        ".env.example",
        "dashboards/prometheus.yml",
        "dashboards/alerts.yml",
        "dashboards/alertmanager.yml",
        "docs/architecture.svg",
        "docs/architecture.mmd",
        "docs/images/infraattack_platform_architecture.png",
        "docs/ResilienceOps_Technical_Documentation.pdf",
        "scripts/generate_example_post_mortem.py",
        "reports/example_incident_memory_exhaustion.md",
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
    assert "Operating the lab on AWS" in readme
    assert "[Installation and quick start](#installation-and-quick-start)" in readme
    assert "[Operating the lab on AWS](#operating-the-lab-on-aws)" in readme
    assert "reports/example_incident_memory_exhaustion.md" in readme
    assert "pre-fix historical" in readme
    assert "# Incident Post-Mortem Report: UNKNOWN_FAULT" not in readme
    assert "Example report" in sample
    assert "Incident Post-Mortem Report: MEMORY_EXHAUSTION" in sample
    assert "POST /fault/reset" in readme
    assert "K8sToolKit.k8s_available" in readme
    assert "bounces the container" not in readme
    assert "MTTD: 2.14s" not in readme
    assert "MTTR: 3.42s" not in readme


def test_architecture_png_is_nontrivial():
    data = (ROOT / "docs/images/infraattack_platform_architecture.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 80_000
