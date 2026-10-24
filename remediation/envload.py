"""Load poller / remediator secrets from .env without overriding the process."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EC2_ENV = Path("/opt/resilienceops/.env")


def _try_parse_dotenv(path: Path) -> dict[str, str] | None:
    """Parsed keys, or None when the file is missing or unreadable.

    PermissionError and other OSError are skipped quietly so a non-root
    poller does not crash or print host secrets.
    """
    try:
        if not path.is_file():
            return None
        lines = path.read_text(encoding="utf-8").splitlines()
    except (PermissionError, OSError):
        return None
    values: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip("'").strip('"')
    return values


def parse_dotenv(path: Path) -> dict[str, str]:
    return _try_parse_dotenv(path) or {}


def load_remediation_env(
    *,
    root: Path | None = None,
    extra: list[Path] | None = None,
) -> list[str]:
    """Read repo `.env`, then the EC2 host `.env`. Existing env wins.

    Unreadable paths (PermissionError / OSError on `/opt/resilienceops/.env`)
    are skipped with no output so a non-root poller cannot leak secrets.
    """
    candidates = [(root or REPO_ROOT) / ".env", EC2_ENV]
    if extra:
        candidates.extend(extra)
    loaded: list[str] = []
    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except (PermissionError, OSError):
            continue
        if resolved in seen:
            continue
        parsed = _try_parse_dotenv(path)
        if parsed is None:
            continue
        seen.add(resolved)
        for key, val in parsed.items():
            if key and os.getenv(key) is None:
                os.environ[key] = val
        loaded.append(str(resolved))
    return loaded
