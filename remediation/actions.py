"""Allowlist, proposal parsing, and execution of the three Path C actions.

Nothing outside ACTIONS / TARGETS can run. Values are matched as whole
tokens (no shell, no extra fields, no path separators).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]

# The only actions this remediator will ever execute.
ACTION_RESET_FAULT = "reset_fault"
ACTION_RESTART_SERVICE = "restart_service"
ACTION_ROLLBACK_DEPLOY = "rollback_deploy"

ACTIONS = frozenset(
    {ACTION_RESET_FAULT, ACTION_RESTART_SERVICE, ACTION_ROLLBACK_DEPLOY}
)

# reset_fault POSTs /fault/reset on each named target (order-service,
# payment-service, or both). That is not Path A FaultCatalog.reset_environment.
RESET_TARGETS = frozenset({"order-service", "payment-service", "both"})

# docker compose restart — app services only. Not redis/postgres/prom/grafana.
RESTART_TARGETS = frozenset({"api-gw", "order-service", "payment-service"})

# rollback_deploy recreates those services from recorded last-good image IDs.
ROLLBACK_TARGETS = frozenset({"api-gw", "order-service", "payment-service", "both"})

APP_SERVICES = frozenset({"api-gw", "order-service", "payment-service"})

PROPOSAL_OPEN = "<!-- resilienceops-proposal:v1 -->"
PROPOSAL_CLOSE = "<!-- /resilienceops-proposal -->"
PROPOSAL_BLOCK = re.compile(
    r"<!--\s*resilienceops-proposal:v1\s*-->(.*?)<!--\s*/resilienceops-proposal\s*-->",
    re.DOTALL | re.IGNORECASE,
)
# One token per line: action: reset_fault
FIELD_LINE = re.compile(r"^(action|target)\s*:\s*(\S+)\s*$", re.IGNORECASE)
# Reject shell / path / URL injection before we even look at the allowlist.
UNSAFE_VALUE = re.compile(
    r"""[;&|`$()<>\\*\n\r\t]|(\.\./)|(\./)|//|https?:|file:""",
    re.IGNORECASE,
)

DEFAULT_STATE_DIR = REPO_ROOT / "logs"
LAST_GOOD_NAME = "last_good_deploy.json"
COMPOSE_BIN = ("docker", "compose")


class RemediationError(ValueError):
    """Raised when a proposal or action is rejected."""


@dataclass(frozen=True)
class Proposal:
    action: str
    target: str

    def as_dict(self) -> dict[str, str]:
        return {"action": self.action, "target": self.target}

    def render(self) -> str:
        return (
            f"{PROPOSAL_OPEN}\n"
            f"action: {self.action}\n"
            f"target: {self.target}\n"
            f"{PROPOSAL_CLOSE}\n"
        )


@dataclass
class ActionResult:
    ok: bool
    action: str
    target: str
    dry_run: bool
    steps: list[dict[str, Any]] = field(default_factory=list)
    verify: dict[str, Any] | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "action": self.action,
            "target": self.target,
            "dry_run": self.dry_run,
            "steps": self.steps,
            "verify": self.verify,
        }
        if self.error:
            payload["error"] = self.error
        return payload


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def validate_proposal_fields(action: str, target: str) -> Proposal:
    """Accept exactly one allowlisted action + one allowlisted target."""
    raw_action, raw_target = action, target
    if UNSAFE_VALUE.search(raw_action or "") or UNSAFE_VALUE.search(raw_target or ""):
        raise RemediationError("rejected unsafe action or target token")
    action = _norm(raw_action)
    target = _norm(raw_target)
    if action not in ACTIONS:
        raise RemediationError(f"unknown action: {raw_action!r}")
    if action == ACTION_RESET_FAULT and target not in RESET_TARGETS:
        raise RemediationError(f"reset_fault target not allowlisted: {raw_target!r}")
    if action == ACTION_RESTART_SERVICE and target not in RESTART_TARGETS:
        raise RemediationError(f"restart_service target not allowlisted: {raw_target!r}")
    if action == ACTION_ROLLBACK_DEPLOY and target not in ROLLBACK_TARGETS:
        raise RemediationError(f"rollback_deploy target not allowlisted: {raw_target!r}")
    return Proposal(action=action, target=target)


def parse_proposal(text: str) -> Proposal:
    """Parse a comment body that names exactly one allowlisted action.

    Rejects missing/multiple proposal blocks, extra fields, blank values,
    and anything that is not `action:` + `target:` tokens.
    """
    if text is None:
        raise RemediationError("empty proposal")
    matches = list(PROPOSAL_BLOCK.finditer(text))
    if not matches:
        raise RemediationError("no resilienceops proposal block")
    if len(matches) != 1:
        raise RemediationError("proposal must name exactly one action")
    body = matches[0].group(1)
    fields: dict[str, str] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if UNSAFE_VALUE.search(line):
            raise RemediationError("rejected unsafe proposal line")
        m = FIELD_LINE.match(line)
        if not m:
            raise RemediationError(f"unsupported proposal line: {line!r}")
        key = m.group(1).lower()
        value = m.group(2)
        if key in fields:
            raise RemediationError(f"duplicate proposal field: {key}")
        fields[key] = value
    extra = set(fields) - {"action", "target"}
    if extra:
        raise RemediationError(f"unsupported proposal fields: {sorted(extra)}")
    if set(fields) != {"action", "target"}:
        raise RemediationError("proposal must include action and target only")
    return validate_proposal_fields(fields["action"], fields["target"])


def latest_proposal(comments: Iterable[str]) -> Proposal:
    """Return the most recent valid proposal (later comments win)."""
    found: Proposal | None = None
    for body in comments:
        if not body or not PROPOSAL_BLOCK.search(body):
            continue
        found = parse_proposal(body)
    if found is None:
        raise RemediationError("no resilienceops proposal block")
    return found


def targets_for(proposal: Proposal) -> list[str]:
    if proposal.target == "both":
        if proposal.action == ACTION_RESTART_SERVICE:
            raise RemediationError("restart_service requires one named service")
        return ["order-service", "payment-service"] if proposal.action == ACTION_RESET_FAULT else sorted(APP_SERVICES)
    return [proposal.target]


def _service_url(name: str) -> str:
    if name == "order-service":
        return os.getenv("ORDER_SERVICE_URL", "http://localhost:8001").rstrip("/")
    if name == "payment-service":
        return os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002").rstrip("/")
    if name == "api-gw":
        return os.getenv("API_GATEWAY_URL", "http://localhost:8000").rstrip("/")
    raise RemediationError(f"no URL for {name}")


def _http_json(method: str, url: str, timeout: float = 8.0) -> dict[str, Any]:
    req = Request(url, method=method, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200)
    except HTTPError as exc:
        raise RemediationError(f"HTTP {exc.code} from {url}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        # ConnectionResetError while a just-restarted container is still
        # binding is retryable; the verify loop treats RemediationError as fail.
        reason = getattr(exc, "reason", exc)
        raise RemediationError(f"request failed: {reason}") from exc
    try:
        body: Any = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        body = {"raw": raw[:200]}
    if not isinstance(body, dict):
        body = {"value": body}
    body["_http_status"] = status
    return body


def _run(argv: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    """Run a fixed argv list (never a shell string)."""
    if not argv or any(not isinstance(part, str) or not part for part in argv):
        raise RemediationError("refusing empty command")
    # Defense in depth: no shell metacharacters in any argv token.
    for part in argv:
        if UNSAFE_VALUE.search(part) and part not in ACTIONS | RESET_TARGETS | RESTART_TARGETS | ROLLBACK_TARGETS:
            # Image IDs are sha256:hex — colon is allowed only after we validate
            # the token shape below. Compose service names are already allowlisted.
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", part) and not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", part
            ):
                raise RemediationError("refusing unsafe command token")
    proc = subprocess.run(
        argv,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


def _compose(*args: str) -> dict[str, Any]:
    if shutil.which("docker") is None:
        raise RemediationError("docker is not installed on this host")
    return _run([*COMPOSE_BIN, *args])


def _state_dir() -> Path:
    raw = (os.getenv("REMEDIATION_STATE_DIR") or "").strip()
    path = Path(raw) if raw else DEFAULT_STATE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def last_good_path() -> Path:
    return _state_dir() / LAST_GOOD_NAME


def _container_image_id(service: str) -> str:
    """Resolve the running compose container's image ID (sha256:…)."""
    listed = _compose("ps", "--format", "json", service)
    if listed["returncode"] != 0:
        raise RemediationError(f"compose ps failed for {service}: {listed['stderr']}")
    rows = []
    blob = listed["stdout"].strip()
    if blob.startswith("["):
        rows = json.loads(blob)
    else:
        for line in blob.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise RemediationError(f"no running container for {service}")
    name = rows[0].get("Name") or rows[0].get("ID")
    if not name:
        raise RemediationError(f"compose ps returned no name for {service}")
    inspected = _run(["docker", "inspect", "-f", "{{.Image}}", name])
    if inspected["returncode"] != 0:
        raise RemediationError(f"docker inspect failed for {service}")
    image_id = inspected["stdout"].strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise RemediationError(f"unexpected image id for {service}")
    return image_id


def record_last_good(services: Iterable[str] | None = None) -> dict[str, Any]:
    """Snapshot currently running image IDs. This is the lab's 'last good deploy'."""
    chosen = list(services) if services is not None else sorted(APP_SERVICES)
    for name in chosen:
        if name not in APP_SERVICES:
            raise RemediationError(f"cannot snapshot unknown service {name!r}")
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "definition": (
            "last good = image IDs of the running Compose app containers at "
            "record time (not a git revert, not an AWS CodeDeploy revision)"
        ),
        "services": {},
    }
    for name in chosen:
        payload["services"][name] = {"image_id": _container_image_id(name)}
    path = last_good_path()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_last_good() -> dict[str, Any]:
    path = last_good_path()
    if not path.is_file():
        raise RemediationError(
            f"no last-good snapshot at {path}; run: python3 remediation/remediate.py record-last-good"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("services"), dict):
        raise RemediationError("last-good snapshot is malformed")
    return data


def _reset_fault(target: str, dry_run: bool) -> list[dict[str, Any]]:
    steps = []
    for name in targets_for(Proposal(ACTION_RESET_FAULT, target)):
        url = f"{_service_url(name)}/fault/reset"
        step: dict[str, Any] = {"kind": "reset_fault", "service": name, "url": url}
        if dry_run:
            step["dry_run"] = True
        else:
            step["response"] = _http_json("POST", url)
        steps.append(step)
    return steps


def _restart_service(target: str, dry_run: bool) -> list[dict[str, Any]]:
    # validate_proposal_fields already restricted target to RESTART_TARGETS.
    step: dict[str, Any] = {"kind": "restart_service", "service": target}
    if dry_run:
        step["dry_run"] = True
        step["argv"] = ["docker", "compose", "restart", target]
        return [step]
    result = _compose("restart", target)
    step.update(result)
    if result["returncode"] != 0:
        raise RemediationError(f"compose restart {target} failed")
    return [step]


def _rollback_override_text(service: str, image_id: str) -> str:
    """Compose overlay that points one service at a recorded image ID."""
    return f"services:\n  {service}:\n    image: {image_id}\n"


def _rollback_deploy(target: str, dry_run: bool) -> list[dict[str, Any]]:
    snapshot = load_last_good()
    steps: list[dict[str, Any]] = []
    names = targets_for(Proposal(ACTION_ROLLBACK_DEPLOY, target))
    compose_file = str(REPO_ROOT / "docker-compose.yml")
    for name in names:
        info = snapshot["services"].get(name)
        if not info or not info.get("image_id"):
            raise RemediationError(f"last-good snapshot has no image for {name}")
        image_id = info["image_id"]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise RemediationError(f"invalid image id in snapshot for {name}")
        override_path = _state_dir() / f"rollback-{name}.yml"
        argv = [
            "docker",
            "compose",
            "-f",
            compose_file,
            "-f",
            str(override_path),
            "up",
            "-d",
            "--no-build",
            "--no-deps",
            "--force-recreate",
            name,
        ]
        step: dict[str, Any] = {
            "kind": "rollback_deploy",
            "service": name,
            "image_id": image_id,
            "override": str(override_path),
            "argv": argv,
        }
        if dry_run:
            step["dry_run"] = True
            steps.append(step)
            continue
        override_path.write_text(_rollback_override_text(name, image_id), encoding="utf-8")
        rec = _run(argv)
        step["recreate"] = {"returncode": rec["returncode"], "stderr": rec["stderr"][-400:]}
        if rec["returncode"] != 0:
            raise RemediationError(f"rollback recreate failed for {name}")
        after = _container_image_id(name)
        step["image_after"] = after
        if after != image_id:
            raise RemediationError(
                f"rollback did not switch {name} to last-good image ({after} != {image_id})"
            )
        steps.append(step)
    return steps


def execute(proposal: Proposal, *, dry_run: bool = False) -> ActionResult:
    """Run exactly one allowlisted action. Never prints secrets."""
    try:
        if proposal.action == ACTION_RESET_FAULT:
            steps = _reset_fault(proposal.target, dry_run)
        elif proposal.action == ACTION_RESTART_SERVICE:
            steps = _restart_service(proposal.target, dry_run)
        elif proposal.action == ACTION_ROLLBACK_DEPLOY:
            steps = _rollback_deploy(proposal.target, dry_run)
        else:
            raise RemediationError(f"unknown action: {proposal.action!r}")
        return ActionResult(
            ok=True,
            action=proposal.action,
            target=proposal.target,
            dry_run=dry_run,
            steps=steps,
        )
    except RemediationError as exc:
        return ActionResult(
            ok=False,
            action=proposal.action,
            target=proposal.target,
            dry_run=dry_run,
            error=str(exc),
        )


def prometheus_base() -> str:
    return os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")


def query_prometheus(expr: str, *, timeout: float = 5.0) -> list[dict[str, Any]]:
    url = f"{prometheus_base()}/api/v1/query?{urlencode({'query': expr})}"
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise RemediationError(f"prometheus query failed: {exc}") from exc
    if payload.get("status") != "success":
        raise RemediationError("prometheus query status was not success")
    return payload.get("data", {}).get("result") or []


def firing_alerts(*, timeout: float = 5.0) -> list[dict[str, Any]]:
    url = f"{prometheus_base()}/api/v1/alerts"
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise RemediationError(f"prometheus alerts failed: {exc}") from exc
    alerts = payload.get("data", {}).get("alerts") or []
    return [a for a in alerts if a.get("state") == "firing"]


def _scalar(results: list[dict[str, Any]]) -> float | None:
    if not results:
        return None
    value = results[0].get("value")
    if not isinstance(value, list) or len(value) < 2:
        return None
    try:
        return float(value[1])
    except (TypeError, ValueError):
        return None


def verify_recovery(proposal: Proposal) -> dict[str, Any]:
    """Confirm Prometheus no longer sees the fault the action was meant to clear."""
    names = targets_for(proposal)
    report: dict[str, Any] = {"ok": True, "checks": []}

    def check(name: str, ok: bool, detail: Any) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            report["ok"] = False

    for name in names:
        if name in {"order-service", "payment-service", "api-gw"}:
            up = _scalar(query_prometheus(f'up{{job="{name}"}}'))
            check(f"up:{name}", up == 1.0, up)
            try:
                health = _http_json("GET", f"{_service_url(name)}/health", timeout=4.0)
                check(f"health:{name}", health.get("_http_status") == 200, health.get("status"))
            except RemediationError as exc:
                check(f"health:{name}", False, str(exc))

    if proposal.action == ACTION_RESET_FAULT and (
        proposal.target in {"order-service", "both"}
    ):
        redis_n = _scalar(query_prometheus("redis_active_connections_count"))
        # alerts.yml RedisConnectionSaturationWarning is >= 40; clean is well below.
        check("redis_active_connections_count<40", redis_n is not None and redis_n < 40, redis_n)

    firing = firing_alerts()
    nameset = set(names)
    blocking = []
    for alert in firing:
        labels = alert.get("labels") or {}
        alertname = labels.get("alertname", "")
        service = labels.get("service") or labels.get("job") or ""
        if alertname == "RedisConnectionSaturation" and (
            proposal.action == ACTION_RESET_FAULT
            and proposal.target in {"order-service", "both"}
        ):
            blocking.append(alertname)
        if alertname == "ServiceDown" and service in nameset:
            blocking.append(f"{alertname}:{service}")
    check("no_blocking_firing_alerts", not blocking, blocking)
    report["firing_alertnames"] = [
        (a.get("labels") or {}).get("alertname") for a in firing
    ]
    return report
