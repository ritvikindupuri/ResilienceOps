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

    monkeypatch.setattr(dr, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(dr, "INCLUDE_PATHS", ["services", "docker-compose.yml", ".env.example", ".env"])

    data = dr.build_deploy_archive(tmp_path)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert ".env" not in names
    assert ".env.example" in names
    assert "docker-compose.yml" in names
