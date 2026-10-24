"""Structured logs that never print secrets."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from remediation.actions import _state_dir

SECRET_KEY = re.compile(r"(token|key|password|secret|authorization|webhook)", re.I)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if SECRET_KEY.search(str(key)):
                out[key] = "[redacted]"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and len(value) > 24 and SECRET_KEY.search(value):
        return "[redacted]"
    return value


def emit(event: dict[str, Any], *, path: Path | None = None) -> dict[str, Any]:
    payload = redact(dict(event))
    payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
    line = json.dumps(payload, sort_keys=True)
    print(line, file=sys.stdout, flush=True)
    dest = path or (_state_dir() / "remediation.jsonl")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return payload
