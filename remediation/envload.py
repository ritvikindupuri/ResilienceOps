"""Load poller / remediator secrets from .env without overriding the process."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EC2_ENV = Path("/opt/sre-colosseum/.env")


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip("'").strip('"')
    return values


def load_remediation_env(
    *,
    root: Path | None = None,
    extra: list[Path] | None = None,
) -> list[str]:
    """Read repo `.env`, then the EC2 host `.env`. Existing env wins."""
    candidates = [(root or REPO_ROOT) / ".env", EC2_ENV]
    if extra:
        candidates.extend(extra)
    loaded: list[str] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        for key, val in parse_dotenv(path).items():
            if key and os.getenv(key) is None:
                os.environ[key] = val
        loaded.append(str(resolved))
    return loaded
