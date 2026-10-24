# Docs assets

The [root README](../README.md) is the **current source of truth** for setup, architecture, alerting, the Grok Bot **AI Incident Diagnosis** template, and the **Incident Remediation** teammate (Diagnosis invokes it; no remediator webhook). Claim-to-evidence (diagram + README vs code): [`ACCURACY.md`](ACCURACY.md).

[ResilienceOps_Technical_Documentation.pdf](ResilienceOps_Technical_Documentation.pdf) is a historical architecture brief (diagrams and earlier design notes). Prefer the README when they disagree — including model IDs in `agents/config.py`, Grafana credentials, Prometheus/Alertmanager localhost binds, and Grok Bot webhook setup.

Images used by the README live in [`images/`](images/).

The current architecture diagram is [`images/infraattack_platform_architecture.png`](images/infraattack_platform_architecture.png). It is rebuilt from official marks in [`icons/`](icons/) (AWS Architecture Icons, CNCF/k3s, brand glyphs) plus [`../scripts/build_architecture.py`](../scripts/build_architecture.py) into [`architecture.svg`](architecture.svg), then rasterized:

```bash
./scripts/render_architecture.sh
```

That script prefers `rsvg-convert` (`librsvg2-bin` on Debian/Ubuntu) and falls back to headless Chrome. Companion mermaid (same flow, no logos): [`architecture.mmd`](architecture.mmd).
