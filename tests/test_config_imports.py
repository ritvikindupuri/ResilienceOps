import os

import pytest

from agents import config


def test_cloudwatch_and_region_exports_exist():
    assert config.AWS_REGION
    assert config.CW_LOG_GROUP_ATTACKER.startswith("/")
    assert config.CW_LOG_GROUP_DEFENDER.startswith("/")
    assert config.CW_LOG_GROUP_INCIDENTS.startswith("/")
    assert config.AI_PROVIDER
    assert config.GEMINI_API_KEY == os.getenv("GEMINI_API_KEY", "")
    assert config.OPENAI_API_KEY == os.getenv("OPENAI_API_KEY", "")


def test_require_ec2_instance_id_errors_when_unset(monkeypatch):
    monkeypatch.delenv("EC2_INSTANCE_ID", raising=False)
    monkeypatch.delenv("SRE_EC2_INSTANCE_ID", raising=False)
    with pytest.raises(RuntimeError, match="EC2_INSTANCE_ID is not set"):
        config.require_ec2_instance_id()


def test_require_ec2_instance_id_reads_env(monkeypatch):
    monkeypatch.setenv("EC2_INSTANCE_ID", "i-testfixture")
    assert config.require_ec2_instance_id() == "i-testfixture"


def test_grafana_auth_requires_both(monkeypatch):
    monkeypatch.delenv("GRAFANA_ADMIN_USER", raising=False)
    monkeypatch.delenv("GRAFANA_ADMIN_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="GRAFANA_ADMIN"):
        config.require_grafana_basic_auth_header()


def test_arena_runner_imports():
    import arena_runner  # noqa: F401
    from agents.attacker.agent import RedTeamAttackerAgent
    from agents.defender.sentinel import BlueTeamSentinel
    from agents.common.cw_logger import CloudWatchLogger

    assert RedTeamAttackerAgent
    assert BlueTeamSentinel
    assert CloudWatchLogger
