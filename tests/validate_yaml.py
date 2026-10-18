#!/usr/bin/env python3
"""Parse Kubernetes and dashboard YAML. Exit non-zero on invalid documents."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "k8s" / "agents" / "agent-sandbox.yaml",
    ROOT / "k8s" / "base" / "namespace-rbac.yaml",
    ROOT / "k8s" / "apps" / "microservices.yaml",
    ROOT / "k8s" / "observability" / "fluentbit-config.yaml",
    ROOT / "docker-compose.yml",
    ROOT / ".pre-commit-config.yaml",
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / "dashboards" / "prometheus.yml",
    ROOT / "dashboards" / "alerts.yml",
    ROOT / "dashboards" / "alertmanager.yml",
]


def main() -> int:
    failed = 0
    for path in TARGETS:
        try:
            with path.open(encoding="utf-8") as handle:
                list(yaml.safe_load_all(handle))
            print(f"OK  {path.relative_to(ROOT)}")
        except Exception as exc:
            failed += 1
            print(f"BAD {path.relative_to(ROOT)}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
