import io
import zipfile
from pathlib import Path

import deploy_remote as dr


def test_build_archive_omits_env(tmp_path, monkeypatch):
    (tmp_path / "services").mkdir()
    (tmp_path / "services" / "readme.txt").write_text("ok", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("version: '3'\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=should-not-be-packed\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")

    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "example.md").write_text("ok", encoding="utf-8")

    monkeypatch.setattr(dr, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        dr,
        "INCLUDE_PATHS",
        ["services", "docker-compose.yml", ".env.example", ".env", "reports"],
    )

    data = dr.build_deploy_archive(tmp_path)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert ".env" not in names
    assert ".env.example" in names
    assert "docker-compose.yml" in names
    assert "reports/example.md" in names


def test_default_include_paths_cover_sandbox_dockerfile_copies():
    assert "reports" in dr.INCLUDE_PATHS
    assert "agents" in dr.INCLUDE_PATHS
    assert "orchestrator.py" in dr.INCLUDE_PATHS
    assert "Dockerfile.agent-sandbox" in dr.INCLUDE_PATHS
