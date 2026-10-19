#!/usr/bin/env python3
"""Build docs/architecture.svg in the Grok-bot-repo icon style.

Logos: Simple Icons (CC0) in docs/icons/. Blobs for Red/Blue/Grok match the
rounded-avatar style used in Ritvik's other Grok bot architecture diagrams.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "docs" / "icons"
OUT = ROOT / "docs" / "architecture.svg"

# Brand fills already set on files; symbols keep viewBox 0 0 24 24.
ICON_FILES = [
    "docker",
    "fastapi",
    "redis",
    "postgresql",
    "prometheus",
    "grafana",
    "kubernetes",
    "github",
    "amazonec2",
    "terraform",
    "python",
]


def icon_inner(name: str) -> str:
    raw = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S)
    if not inner:
        raise SystemExit(f"could not parse {name}.svg")
    return inner.group(1).strip()


def symbols() -> str:
    chunks = []
    for name in ICON_FILES:
        chunks.append(f'    <symbol id="i-{name}" viewBox="0 0 24 24">{icon_inner(name)}</symbol>')
    # Person silhouette for owner ping (not a trademarked mark).
    chunks.append(
        """    <symbol id="i-person" viewBox="0 0 24 24">
      <circle cx="12" cy="8" r="4" fill="#4B5563"/>
      <path fill="#4B5563" d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7v1H4z"/>
    </symbol>"""
    )
    return "\n".join(chunks)


def node(x: float, y: float, icon: str, name: str, cap: str) -> str:
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="-26" y="-58" width="52" height="52"/>
    <text class="name" y="14" text-anchor="middle">{name}</text>
    <text class="cap" y="32" text-anchor="middle">{cap}</text>
  </g>"""


def blob(x: float, y: float, fill: str, name: str, cap: str) -> str:
    # Organic rounded blob + two eyes, same family as the other Grok bot diagrams.
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <ellipse cx="0" cy="-18" rx="30" ry="26" fill="{fill}"/>
    <circle cx="-9" cy="-22" r="4.2" fill="#FFFFFF"/>
    <circle cx="9" cy="-22" r="4.2" fill="#FFFFFF"/>
    <text class="name" y="24" text-anchor="middle">{name}</text>
    <text class="cap" y="42" text-anchor="middle">{cap}</text>
  </g>"""


def group(x: float, y: float, w: float, h: float, label: str) -> str:
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="22" fill="#F8FAFC" stroke="#E5E7EB"/>\n'
        f'  <text x="{x + 22:.0f}" y="{y + 28:.0f}" class="group">{label}</text>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    return (
        f'  <line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
        f'class="arrow"{dash} marker-end="url(#arr)"/>'
    )


def pill(x: float, y: float, text: str) -> str:
    w = max(72, 7.2 * len(text) + 18)
    return f"""  <g transform="translate({x - w / 2:.1f},{y - 10:.0f})">
    <rect width="{w:.1f}" height="20" rx="10" fill="#FFFFFF" stroke="#D1D5DB"/>
    <text x="{w / 2:.1f}" y="14" text-anchor="middle" class="pill">{text}</text>
  </g>"""


def build() -> str:
    # Canvas sized for README (~950px display of a 1920-wide source).
    W, H = 1920, 1000

    # Left column: AWS host + k3s
    # Center: compose lab  |  Right: Grok bot
    g_aws = group(36, 72, 268, 150, "AWS host")
    g_k3s = group(36, 238, 268, 394, "k3s sandbox")
    g_lab = group(324, 72, 980, 560, "Compose lab")
    g_bot = group(1324, 72, 560, 560, "Your Grok bot")

    nodes = [
        node(104, 152, "terraform", "Terraform", "One-file deploy"),
        node(236, 152, "amazonec2", "EC2", "Lab host"),
        node(170, 310, "kubernetes", "k3s", "Agent sandbox"),
        blob(170, 430, "#EF4444", "Red Team", "Injects faults"),
        blob(170, 560, "#3B82F6", "Blue Team", "Detects and resets"),
        node(430, 190, "docker", "Traffic", "Live load"),
        node(590, 190, "fastapi", "api-gw", "Gateway"),
        node(760, 190, "fastapi", "order-service", "Orders"),
        node(930, 190, "fastapi", "payment-service", "Payments"),
        node(760, 325, "redis", "Redis", "Cache"),
        node(930, 325, "postgresql", "PostgreSQL", "Orders DB"),
        node(520, 460, "prometheus", "Prometheus", "Scrapes + rules"),
        node(520, 580, "grafana", "Grafana", "Reads Prometheus"),
        node(780, 460, "prometheus", "Alertmanager", "Groups alerts"),
        node(1080, 460, "python", "incident-bridge", "Adds evidence"),
        blob(1604, 210, "#14B8A6", "Grok bot", "AI Incident Diagnosis"),
        node(1480, 430, "github", "GitHub issue", "label: incident"),
        node(1728, 430, "person", "Owner ping", "Firing critical"),
    ]

    parts = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"
     aria-label="How ResilienceOps plus AI Incident Diagnosis works">
  <defs>
    <style>
      .title {{ font: 700 28px Arial, Helvetica, sans-serif; fill: #111827; }}
      .group {{ font: 600 13px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .name {{ font: 700 14px Arial, Helvetica, sans-serif; fill: #111827; }}
      .cap {{ font: 12px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .pill {{ font: 600 11px Arial, Helvetica, sans-serif; fill: #4B5563; }}
      .gate {{ font: 600 14px Arial, Helvetica, sans-serif; fill: #4B5563; }}
      .gate-sub {{ font: 12px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .card-n {{ font: 700 14px Arial, Helvetica, sans-serif; fill: #C2410C; }}
      .card-t {{ font: 13px Arial, Helvetica, sans-serif; fill: #1F2937; }}
      .arrow {{ stroke: #9CA3AF; stroke-width: 1.8; fill: none; }}
    </style>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#9CA3AF"/>
    </marker>
{symbols()}
  </defs>
  <rect width="{W}" height="{H}" fill="#FFFFFF"/>
  <text x="{W/2:.0f}" y="44" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
'''
    ]
    parts.append(g_aws)
    parts.append(g_k3s)
    parts.append(g_lab)
    parts.append(g_bot)
    parts.extend(nodes)

    # Request path
    parts.append(arrow(462, 180, 554, 180))
    parts.append(arrow(622, 180, 714, 180))
    parts.append(arrow(792, 180, 884, 180))
    parts.append(arrow(760, 224, 760, 283))
    parts.append(arrow(930, 224, 930, 283))
    # Metrics scrape into Prometheus
    parts.append(
        '  <polyline points="845,365 845,400 520,400 520,412" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    # Alert path (Grafana hangs off Prometheus so it is not in this chain)
    parts.append(arrow(562, 450, 738, 450))
    parts.append(arrow(822, 450, 1038, 450))
    parts.append(arrow(520, 492, 520, 532))
    # Bridge -> Grok
    parts.append(
        '  <polyline points="1122,450 1288,450 1288,192 1570,192" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    parts.append(arrow(1570, 250, 1480, 388))
    parts.append(arrow(1638, 250, 1728, 388))
    # Red injects into the service row; Blue probes/resets via api-gw.
    parts.append(
        '  <polyline points="200,412 318,412 318,168 394,168" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    parts.append(
        '  <polyline points="200,548 318,548 318,230 548,230" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )

    parts.append(pill(530, 152, "requests"))
    parts.append(pill(250, 396, "faults"))
    parts.append(pill(250, 532, "detect / reset"))
    parts.append(pill(700, 388, "metrics"))
    parts.append(pill(650, 434, "firing alerts"))
    parts.append(pill(575, 512, "PromQL"))
    parts.append(pill(1220, 434, "enriched JSON"))
    parts.append(pill(1660, 308, "read-only"))

    # Gate
    parts.append(
        '  <rect x="36" y="656" width="1848" height="56" rx="18" fill="#FFFFFF" '
        'stroke="#D1D5DB" stroke-dasharray="7 6"/>'
    )
    parts.append(
        '  <text x="960" y="680" text-anchor="middle" class="gate">'
        "Read-only: the bot never restarts, scales, or pushes</text>"
    )
    parts.append(
        '  <text x="960" y="698" text-anchor="middle" class="gate-sub">'
        "Path A (Red/Blue on k3s) may reset faults. The Grok bot only diagnoses and files issues.</text>"
    )

    # Step cards — wrap long text with two tspans
    def card2(n: int, x: float, line1: str, line2: str) -> str:
        return f"""  <g transform="translate({x:.0f},736)">
    <rect width="592" height="80" rx="14" fill="#FFF7ED" stroke="#FDBA74"/>
    <text x="20" y="34" class="card-n">{n}.</text>
    <text x="44" y="34" class="card-t">{line1}</text>
    <text x="44" y="56" class="card-t">{line2}</text>
  </g>"""

    parts.append(card2(1, 36, "Fault or real outage trips a", "Prometheus alert rule."))
    parts.append(card2(2, 664, "Bridge adds evidence and posts", "enriched JSON to your bot."))
    parts.append(card2(3, 1292, "Bot diagnoses and files or", "updates a GitHub issue."))

    parts.append("</svg>\n")
    return "\n".join(parts)


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
