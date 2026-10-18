# Docs assets

The [root README](../README.md) is the **current source of truth** for setup, architecture, alerting, and the Grok Bot **AI Incident Diagnosis** template.

[ResilienceOps_Technical_Documentation.pdf](ResilienceOps_Technical_Documentation.pdf) is a historical architecture brief (diagrams and earlier design notes). Prefer the README when they disagree — including model IDs in `agents/config.py`, Grafana credentials, Prometheus/Alertmanager localhost binds, and Grok Bot webhook setup.

Images used by the README live in [`images/`](images/).

The current architecture diagram is [`images/infraattack_platform_architecture.png`](images/infraattack_platform_architecture.png). Canonical source is [`architecture.svg`](architecture.svg). Render:

```bash
./scripts/render_architecture.sh
```

That script prefers `rsvg-convert` (`librsvg2-bin` on Debian/Ubuntu) and falls back to headless Chrome. Companion mermaid source: [`architecture.mmd`](architecture.mmd) (not used for the PNG; column layout is easier in SVG).
