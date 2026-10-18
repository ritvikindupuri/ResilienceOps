"""Validate Prometheus alerting rules and Alertmanager routing config."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from agents import config

ROOT = Path(__file__).resolve().parents[1]
ALERTS = ROOT / "dashboards" / "alerts.yml"
ALERTMANAGER = ROOT / "dashboards" / "alertmanager.yml"
PROMETHEUS = ROOT / "dashboards" / "prometheus.yml"
PROM_IMAGE = "prom/prometheus:v2.52.0"
AM_IMAGE = "prom/alertmanager:v0.27.0"

REQUIRED_ALERTS = {
    "ServiceDown",
    "APIGatewayHighErrorRate",
    "OrderServiceHighErrorRate",
    "PaymentServiceHighErrorRate",
    "APIGatewayP99LatencySLO",
    "OrderServiceP99LatencySLO",
    "PaymentServiceP99LatencySLO",
    "OrderServiceMemoryLeak",
    "OrderServiceMemoryLeakCritical",
    "RedisConnectionSaturationWarning",
    "RedisConnectionSaturation",
    "PaymentServiceOutage",
    "PaymentServiceLatencyHigh",
}


def _rules():
    docs = list(yaml.safe_load_all(ALERTS.read_text(encoding="utf-8")))
    assert docs and docs[0].get("groups")
    rules = []
    for group in docs[0]["groups"]:
        for rule in group.get("rules") or []:
            rules.append(rule)
    return rules


def test_prometheus_wires_rule_files_and_alertmanager():
    conf = yaml.safe_load(PROMETHEUS.read_text(encoding="utf-8"))
    assert "/etc/prometheus/alerts.yml" in (conf.get("rule_files") or [])
    targets = []
    for am in conf.get("alerting", {}).get("alertmanagers", []):
        for item in am.get("static_configs") or []:
            targets.extend(item.get("targets") or [])
    assert "alertmanager:9093" in targets


def test_alert_rules_have_required_labels_and_thresholds():
    rules = _rules()
    names = {rule["alert"] for rule in rules if "alert" in rule}
    missing = REQUIRED_ALERTS - names
    assert not missing, f"missing alerts: {sorted(missing)}"

    slo_latency_s = config.SLO_MAX_P99_LATENCY_MS / 1000.0
    slo_error = config.SLO_MAX_ERROR_RATE_PERCENT
    text = ALERTS.read_text(encoding="utf-8")
    assert str(slo_latency_s) in text
    assert str(int(slo_error)) in text or str(slo_error) in text
    assert "maxclients" in text.lower() or "50" in text

    for rule in rules:
        if "alert" not in rule:
            continue
        assert "expr" in rule and str(rule["expr"]).strip()
        assert "for" in rule
        labels = rule.get("labels") or {}
        assert labels.get("severity") in {"critical", "warning"}
        assert labels.get("service")
        annotations = rule.get("annotations") or {}
        assert annotations.get("summary")
        assert annotations.get("description")


def test_compose_binds_alertmanager_and_bridge_to_localhost():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert "127.0.0.1:9093:9093" in services["alertmanager"]["ports"]
    assert "127.0.0.1:8088:8080" in services["incident-bridge"]["ports"]
    assert "127.0.0.1:9090:9090" in services["prometheus"]["ports"]
    assert "dashboards/alerts.yml:/etc/prometheus/alerts.yml" in " ".join(
        services["prometheus"]["volumes"]
    )


def test_alertmanager_routes_webhook_with_send_resolved():
    conf = yaml.safe_load(ALERTMANAGER.read_text(encoding="utf-8"))
    route = conf["route"]
    assert route["receiver"] == "incident-bridge"
    assert route["group_wait"]
    assert route["group_interval"]
    assert route["repeat_interval"]
    receivers = {item["name"]: item for item in conf["receivers"]}
    webhook = receivers["incident-bridge"]["webhook_configs"][0]
    assert webhook["url"] == "http://incident-bridge:8080/webhook"
    assert webhook["send_resolved"] is True


def _docker_image_available(image: str) -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    inspect = subprocess.run(
        [docker, "image", "inspect", image],
        capture_output=True,
        timeout=15,
        check=False,
    )
    if inspect.returncode == 0:
        return True
    pull = subprocess.run(
        [docker, "pull", image],
        capture_output=True,
        timeout=180,
        check=False,
    )
    return pull.returncode == 0


def test_promtool_check_rules_when_available():
    if not _docker_image_available(PROM_IMAGE):
        pytest.skip("pinned prom/prometheus image is not available")
    docker = shutil.which("docker")
    result = subprocess.run(
        [
            docker,
            "run",
            "--rm",
            "-v",
            f"{ALERTS}:/etc/prometheus/alerts.yml:ro",
            "--entrypoint",
            "/bin/promtool",
            PROM_IMAGE,
            "check",
            "rules",
            "/etc/prometheus/alerts.yml",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_amtool_check_config_when_available():
    if not _docker_image_available(AM_IMAGE):
        pytest.skip("pinned prom/alertmanager image is not available")
    docker = shutil.which("docker")
    result = subprocess.run(
        [
            docker,
            "run",
            "--rm",
            "-v",
            f"{ALERTMANAGER}:/etc/alertmanager/alertmanager.yml:ro",
            "--entrypoint",
            "/bin/amtool",
            AM_IMAGE,
            "check-config",
            "/etc/alertmanager/alertmanager.yml",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
