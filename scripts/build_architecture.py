#!/usr/bin/env python3
"""Build docs/architecture.svg in the Grok-bot-repo icon style.

Official marks live in docs/icons/ (AWS Architecture Icons, CNCF/k3s,
Grafana plugin Alertmanager, Simple Icons brand glyphs). Generic person /
clock / bell / document / traffic symbols are drawn here. The Grok bot
avatar copies the rounded Identity Mapper hexagon from
https://github.com/ritvikindupuri/grok-bot-aws-attack-path-team
(docs/architecture.png) and recolors it to #FF3E51.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "docs" / "icons"
OUT = ROOT / "docs" / "architecture.svg"

GROK_RED = "#FF3E51"

# Official SVG files. viewBox is read from each file.
ICON_FILES = [
    "docker",
    "fastapi",
    "redis",
    "postgresql",
    "prometheus",
    "grafana",
    "k3s",
    "github",
    "aws-ec2",
    "aws-iam",
    "aws-ssm",
    "terraform",
    "alertmanager",
]


def prefix_ids(svg: str, prefix: str) -> str:
    """Make id / url(#id) / class names unique so symbols can share a page."""
    ids = re.findall(r'\bid="([^"]+)"', svg)
    for raw_id in dict.fromkeys(ids):
        new = f"{prefix}{raw_id}"
        svg = svg.replace(f'id="{raw_id}"', f'id="{new}"')
        svg = svg.replace(f"url(#{raw_id})", f"url(#{new})")
        svg = svg.replace(f'href="#{raw_id}"', f'href="#{new}"')
        svg = svg.replace(f'xlink:href="#{raw_id}"', f'xlink:href="#{new}"')
    classes = re.findall(r"\.([A-Za-z_][\w-]*)\s*\{", svg)
    for cls in dict.fromkeys(classes):
        new = f"{prefix}{cls}"
        svg = re.sub(rf"\.{re.escape(cls)}\b", f".{new}", svg)
        svg = re.sub(
            rf'class="([^"]*)"',
            lambda m, n=new, c=cls: 'class="'
            + re.sub(rf"\b{re.escape(c)}\b", n, m.group(1))
            + '"',
            svg,
        )
    return svg


def icon_symbol(name: str) -> str:
    raw = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    raw = re.sub(r"<!DOCTYPE[^>]*>", "", raw, flags=re.S)
    vb = re.search(r'viewBox="([^"]+)"', raw)
    width = re.search(r'\bwidth="([\d.]+)(?:px)?"', raw)
    height = re.search(r'\bheight="([\d.]+)(?:px)?"', raw)
    if vb:
        view_box = vb.group(1)
    elif width and height:
        view_box = f"0 0 {width.group(1)} {height.group(1)}"
    else:
        view_box = "0 0 24 24"
    inner = re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S)
    if not inner:
        raise SystemExit(f"could not parse {name}.svg")
    body = prefix_ids(inner.group(1).strip(), f"{name}-")
    return f'    <symbol id="i-{name}" viewBox="{view_box}">{body}</symbol>'


def generic_symbols() -> str:
    # Plain generic marks (not trademarked product logos).
    return """    <symbol id="i-person" viewBox="0 0 24 24">
      <circle cx="12" cy="8" r="4" fill="#4B5563"/>
      <path fill="#4B5563" d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7v1H4z"/>
    </symbol>
    <symbol id="i-person-red" viewBox="0 0 24 24">
      <circle cx="12" cy="8" r="4" fill="#EF4444"/>
      <path fill="#EF4444" d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7v1H4z"/>
    </symbol>
    <symbol id="i-person-blue" viewBox="0 0 24 24">
      <circle cx="12" cy="8" r="4" fill="#3B82F6"/>
      <path fill="#3B82F6" d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7v1H4z"/>
    </symbol>
    <symbol id="i-bell" viewBox="0 0 24 24">
      <path fill="#4B5563" d="M12 3a6 6 0 00-6 6v2.2L4 15h16l-2-3.8V9a6 6 0 00-6-6z"/>
      <path fill="#4B5563" d="M9.5 17.2a2.5 2.5 0 005 0z"/>
    </symbol>
    <symbol id="i-document" viewBox="0 0 24 24">
      <path fill="#6B7280" d="M6 2h9l5 5v15H6z"/>
      <path fill="#E5E7EB" d="M15 2v5h5"/>
      <path stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" d="M9 12h8M9 16h6"/>
    </symbol>
    <symbol id="i-traffic" viewBox="0 0 24 24">
      <rect x="8" y="1.5" width="8" height="21" rx="4" fill="#111827"/>
      <circle cx="12" cy="6.2" r="2.3" fill="#EF4444"/>
      <circle cx="12" cy="12" r="2.3" fill="#F59E0B"/>
      <circle cx="12" cy="17.8" r="2.3" fill="#22C55E"/>
    </symbol>
    <symbol id="i-clock" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="9" fill="none" stroke="#4B5563" stroke-width="1.8"/>
      <path stroke="#4B5563" stroke-width="1.8" stroke-linecap="round" d="M12 7v5l3.2 2"/>
    </symbol>"""


def symbols() -> str:
    chunks = [icon_symbol(name) for name in ICON_FILES]
    chunks.append(generic_symbols())
    return "\n".join(chunks)


def node(x: float, y: float, icon: str, name: str, cap: str, size: float = 52) -> str:
    top = -size - 6
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{top:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" y="14" text-anchor="middle">{name}</text>
    <text class="cap" y="32" text-anchor="middle">{cap}</text>
  </g>"""


def _rounded_hexagon_path(radius: float = 30, corner: float = 10.5) -> str:
    """Pointy-top hexagon with quadratic corner rounding (Identity Mapper shape)."""
    verts = []
    for i in range(6):
        ang = math.radians(-90 + i * 60)
        verts.append((radius * math.cos(ang), radius * math.sin(ang)))

    def _sub(a, b):
        return (a[0] - b[0], a[1] - b[1])

    def _add(a, b):
        return (a[0] + b[0], a[1] + b[1])

    def _mul(a, s):
        return (a[0] * s, a[1] * s)

    def _unit(a):
        mag = math.hypot(a[0], a[1]) or 1.0
        return (a[0] / mag, a[1] / mag)

    parts: list[str] = []
    n = 6
    for i in range(n):
        prev, cur, nxt = verts[i - 1], verts[i], verts[(i + 1) % n]
        p1 = _add(cur, _mul(_unit(_sub(prev, cur)), corner))
        p2 = _add(cur, _mul(_unit(_sub(nxt, cur)), corner))
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd} {p1[0]:.2f},{p1[1]:.2f}")
        parts.append(f"Q {cur[0]:.2f},{cur[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}")
    parts.append("Z")
    return " ".join(parts)


def grok_avatar(x: float, y: float, name: str, cap: str) -> str:
    """Rounded pointy-top hexagon + two small slanted white eyes.

    Geometry copies the violet Identity Mapper hexagon in the 1024px
    AWS attack-path architecture.png (around x=270-340, y=400-470):
    regular hexagon, rounded corners, eyes as short ovals rotated
    clockwise so the right mark sits slightly higher. Recolored #FF3E51.
    """
    path = _rounded_hexagon_path()
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <g transform="translate(0,-24)">
      <path d="{path}" fill="{GROK_RED}"/>
      <g transform="translate(0,-4) rotate(16)">
        <ellipse cx="-6.2" cy="0" rx="3.6" ry="5.0" fill="#FFFFFF"/>
        <ellipse cx="6.2" cy="0" rx="3.6" ry="5.0" fill="#FFFFFF"/>
      </g>
    </g>
    <text class="name" y="28" text-anchor="middle">{name}</text>
    <text class="cap" y="46" text-anchor="middle">{cap}</text>
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
    W, H = 1920, 1000

    g_aws = group(36, 72, 280, 228, "AWS host")
    g_k3s = group(36, 316, 280, 316, "k3s sandbox")
    g_lab = group(336, 72, 968, 560, "Compose lab")
    g_bot = group(1324, 72, 560, 560, "Your Grok bot")

    nodes = [
        node(106, 148, "terraform", "Terraform", "One-file deploy"),
        node(220, 148, "aws-ec2", "EC2", "Lab host"),
        node(106, 248, "aws-iam", "IAM", "Instance role"),
        node(220, 248, "aws-ssm", "SSM", "Host access"),
        node(176, 392, "k3s", "k3s", "Agent sandbox"),
        node(176, 492, "person-red", "Red Team", "Injects faults"),
        node(176, 584, "person-blue", "Blue Team", "Detects and resets"),
        node(430, 190, "traffic", "Traffic", "Live load"),
        node(590, 190, "fastapi", "api-gw", "Gateway"),
        node(760, 190, "fastapi", "order-service", "Orders"),
        node(930, 190, "fastapi", "payment-service", "Payments"),
        node(760, 325, "redis", "Redis", "Cache"),
        node(930, 325, "postgresql", "PostgreSQL", "Orders DB"),
        node(1090, 325, "docker", "Docker", "Compose stack"),
        node(520, 460, "prometheus", "Prometheus", "Scrapes + rules"),
        node(520, 580, "grafana", "Grafana", "Reads Prometheus"),
        node(780, 460, "alertmanager", "Alertmanager", "Groups alerts"),
        node(1080, 460, "document", "incident-bridge", "Adds evidence"),
        grok_avatar(1604, 214, "AI Incident Diagnosis", "Your Grok bot"),
        node(1480, 430, "github", "GitHub issue", "label: incident"),
        node(1728, 430, "bell", "Owner ping", "Firing critical"),
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
  <text x="{W / 2:.0f}" y="44" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
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
    parts.append(arrow(1570, 258, 1480, 388))
    parts.append(arrow(1638, 258, 1728, 388))
    # Red injects into the service row; Blue probes/resets via api-gw.
    parts.append(
        '  <polyline points="206,480 330,480 330,168 394,168" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    parts.append(
        '  <polyline points="206,572 330,572 330,230 548,230" fill="none" class="arrow" marker-end="url(#arr)"/>'
    )

    parts.append(pill(530, 152, "requests"))
    parts.append(pill(258, 464, "faults"))
    parts.append(pill(258, 556, "detect / reset"))
    parts.append(pill(700, 388, "metrics"))
    parts.append(pill(650, 434, "firing alerts"))
    parts.append(pill(575, 512, "PromQL"))
    parts.append(pill(1220, 434, "enriched JSON"))
    parts.append(pill(1660, 318, "read-only"))

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
