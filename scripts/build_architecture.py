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

# ~1.3x the previous 52px marks / 14px names so the figure reads at README width.
ICON = 68
LABEL_BAND = 56  # group title has this band to itself; icons start below it

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


def node(x: float, y: float, icon: str, name: str, cap: str, size: float = ICON) -> str:
    # Icon sits above the name; caller must place y so the icon stays below the group label.
    top = -size - 8
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{top:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" y="18" text-anchor="middle">{name}</text>
    <text class="cap" y="40" text-anchor="middle">{cap}</text>
  </g>"""


def _rounded_hexagon_path(radius: float = 40, corner: float = 13) -> str:
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
    """Rounded pointy-top hexagon + two small slanted white capsule eyes.

    Eyes match the Identity Mapper bot in the attack-path architecture.png:
    short stadium capsules, rotated clockwise so the right mark sits higher.
    """
    path = _rounded_hexagon_path()
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <g transform="translate(0,-28)">
      <path d="{path}" fill="{GROK_RED}"/>
      <g transform="translate(0,-5) rotate(28)">
        <rect x="-12.2" y="-7.2" width="5.6" height="14.4" rx="2.8" fill="#FFFFFF"/>
        <rect x="6.6" y="-7.2" width="5.6" height="14.4" rx="2.8" fill="#FFFFFF"/>
      </g>
    </g>
    <text class="name" y="36" text-anchor="middle">{name}</text>
    <text class="cap" y="58" text-anchor="middle">{cap}</text>
  </g>"""


def group(x: float, y: float, w: float, h: float, label: str) -> str:
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="22" fill="#F8FAFC" stroke="#E5E7EB"/>\n'
        f'  <text x="{x + 24:.0f}" y="{y + 34:.0f}" class="group">{label}</text>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    return (
        f'  <line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
        f'class="arrow"{dash} marker-end="url(#arr)"/>'
    )


def pill(x: float, y: float, text: str) -> str:
    w = max(88, 8.6 * len(text) + 22)
    return f"""  <g transform="translate({x - w / 2:.1f},{y - 12:.0f})">
    <rect width="{w:.1f}" height="24" rx="12" fill="#FFFFFF" stroke="#D1D5DB"/>
    <text x="{w / 2:.1f}" y="17" text-anchor="middle" class="pill">{text}</text>
  </g>"""


def build() -> str:
    W, H = 1920, 1100

    # Shared vertical band for the four groups so the bot column can be centered.
    gy = 64
    aws_h = 318
    gap = 16
    k3s_y = gy + aws_h + gap
    k3s_h = 468
    col_bottom = k3s_y + k3s_h  # 866
    lab_h = col_bottom - gy  # 802

    g_aws = group(36, gy, 304, aws_h, "AWS host")
    g_k3s = group(36, k3s_y, 304, k3s_h, "k3s sandbox")
    g_lab = group(356, gy, 948, lab_h, "Compose lab")
    g_bot = group(1320, gy, 564, lab_h, "Your Grok bot")

    # First icon top = group_y + LABEL_BAND. node y = icon_top + ICON + 8.
    aws_r1 = gy + LABEL_BAND + ICON + 8  # 196
    aws_r2 = aws_r1 + ICON + 8 + 40 + 16  # 328
    k3s_r1 = k3s_y + LABEL_BAND + ICON + 8
    k3s_pitch = ICON + 8 + 40 + 28
    k3s_r2 = k3s_r1 + k3s_pitch
    k3s_r3 = k3s_r2 + k3s_pitch

    lab_r1 = gy + LABEL_BAND + ICON + 8  # 196, aligned with AWS row 1
    lab_r2 = lab_r1 + 176  # redis / postgres / docker (gap under the metrics rail)
    lab_r3 = lab_r2 + 160  # prometheus / alertmanager / bridge
    lab_r4 = lab_r3 + 148  # grafana under prometheus

    # Vertically center the bot stack in the group (below the label band).
    # Leave enough gap under the caption so outgoing arrows travel down, not
    # through the label.
    bot_cx = 1602
    bot_inner_top = gy + LABEL_BAND
    bot_inner_bot = gy + lab_h - 24
    bot_stack_h = 68 + 64 + 88 + ICON + 8 + 40  # avatar + arrow gap + github row
    bot_avatar_y = bot_inner_top + (bot_inner_bot - bot_inner_top - bot_stack_h) / 2 + 68
    bot_row_y = bot_avatar_y + 228

    nodes = [
        node(112, aws_r1, "terraform", "Terraform", "One-file deploy"),
        node(254, aws_r1, "aws-ec2", "EC2", "Lab host"),
        node(112, aws_r2, "aws-iam", "IAM", "Instance role"),
        node(254, aws_r2, "aws-ssm", "SSM", "Host access"),
        node(188, k3s_r1, "k3s", "k3s", "Agent sandbox"),
        node(188, k3s_r2, "person-red", "Red Team", "Injects faults"),
        node(188, k3s_r3, "person-blue", "Blue Team", "Detects and resets"),
        node(456, lab_r1, "traffic", "Traffic", "Live load"),
        node(628, lab_r1, "fastapi", "api-gw", "Gateway"),
        node(828, lab_r1, "fastapi", "order-service", "Orders"),
        node(1036, lab_r1, "fastapi", "payment-service", "Payments"),
        node(828, lab_r2, "redis", "Redis", "Cache"),
        node(1036, lab_r2, "postgresql", "PostgreSQL", "Orders DB"),
        node(1210, lab_r2, "docker", "Docker", "Compose stack"),
        node(628, lab_r3, "prometheus", "Prometheus", "Scrapes + rules"),
        node(628, lab_r4, "grafana", "Grafana", "Reads Prometheus"),
        node(900, lab_r3, "alertmanager", "Alertmanager", "Groups alerts"),
        node(1148, lab_r3, "document", "incident-bridge", "Adds evidence"),
        grok_avatar(bot_cx, bot_avatar_y, "AI Incident Diagnosis", "Your Grok bot"),
        node(1468, bot_row_y, "github", "GitHub issue", "label: incident"),
        node(1736, bot_row_y, "bell", "Owner ping", "Firing critical"),
    ]

    parts = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"
     aria-label="How ResilienceOps plus AI Incident Diagnosis works">
  <defs>
    <style>
      .title {{ font: 700 36px Arial, Helvetica, sans-serif; fill: #111827; }}
      .group {{ font: 600 17px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .name {{ font: 700 18px Arial, Helvetica, sans-serif; fill: #111827; }}
      .cap {{ font: 16px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .pill {{ font: 600 14px Arial, Helvetica, sans-serif; fill: #4B5563; }}
      .gate {{ font: 600 18px Arial, Helvetica, sans-serif; fill: #4B5563; }}
      .gate-sub {{ font: 16px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .card-n {{ font: 700 18px Arial, Helvetica, sans-serif; fill: #C2410C; }}
      .card-t {{ font: 17px Arial, Helvetica, sans-serif; fill: #1F2937; }}
      .arrow {{ stroke: #9CA3AF; stroke-width: 2.2; fill: none; }}
    </style>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#9CA3AF"/>
    </marker>
{symbols()}
  </defs>
  <rect width="{W}" height="{H}" fill="#FFFFFF"/>
  <text x="{W / 2:.0f}" y="46" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
'''
    ]
    parts.append(g_aws)
    parts.append(g_k3s)
    parts.append(g_lab)
    parts.append(g_bot)
    parts.extend(nodes)

    # Request path (icon vertical center is node_y - ICON/2 - 4).
    ic = lab_r1 - ICON / 2 - 4  # ~158
    parts.append(arrow(490, ic, 594, ic))
    parts.append(arrow(662, ic, 794, ic))
    parts.append(arrow(862, ic, 1002, ic))
    # One metrics rail under the three FastAPI services, then straight down
    # the api-gw column to Prometheus. Redis/Postgres arrows start below the rail.
    bar_y = lab_r1 + 50
    prom_top = lab_r3 - ICON - 8
    parts.append(
        f'  <line x1="628" y1="{bar_y:.0f}" x2="1036" y2="{bar_y:.0f}" class="arrow"/>'
    )
    parts.append(arrow(628, bar_y, 628, prom_top))
    parts.append(pill(710, (bar_y + prom_top) / 2, "metrics"))
    parts.append(arrow(828, bar_y + 10, 828, lab_r2 - ICON - 8))
    parts.append(arrow(1036, bar_y + 10, 1036, lab_r2 - ICON - 8))

    # Alert path
    am_ic = lab_r3 - ICON / 2 - 4
    parts.append(arrow(662, am_ic, 866, am_ic))
    parts.append(arrow(934, am_ic, 1114, am_ic))
    parts.append(arrow(628, lab_r3 + 44, 628, lab_r4 - ICON - 8))

    # Bridge → Grok hexagon (incoming hits the avatar, not the caption)
    hex_cy = bot_avatar_y - 28
    parts.append(
        f'  <polyline points="1182,{am_ic:.0f} 1304,{am_ic:.0f} 1304,{hex_cy:.0f} 1560,{hex_cy:.0f}" '
        f'fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    # Fork from a point below the caption (name +36, cap +58) down to the icons.
    out_y = bot_avatar_y + 78
    gh_top = bot_row_y - ICON - 8
    parts.append(arrow(bot_cx, out_y, 1468, gh_top))
    parts.append(arrow(bot_cx, out_y, 1736, gh_top))

    # Red injects into order-service; Blue probes/resets via api-gw.
    red_ic = k3s_r2 - ICON / 2 - 4
    blue_ic = k3s_r3 - ICON / 2 - 4
    parts.append(
        f'  <polyline points="222,{red_ic:.0f} 340,{red_ic:.0f} 340,{ic:.0f} 422,{ic:.0f}" '
        f'fill="none" class="arrow" marker-end="url(#arr)"/>'
    )
    parts.append(
        f'  <polyline points="222,{blue_ic:.0f} 340,{blue_ic:.0f} 340,{ic + 36:.0f} 594,{ic + 36:.0f}" '
        f'fill="none" class="arrow" marker-end="url(#arr)"/>'
    )

    parts.append(pill(544, ic - 22, "requests"))
    parts.append(pill(280, red_ic, "faults"))
    parts.append(pill(280, blue_ic, "detect / reset"))
    parts.append(pill(950, am_ic - 22, "firing alerts"))
    parts.append(pill(828, (lab_r3 + 44 + lab_r4 - ICON - 8) / 2, "PromQL"))
    parts.append(pill(1288, am_ic - 22, "enriched JSON"))
    parts.append(pill(bot_cx + 90, (out_y + gh_top) / 2, "read-only"))

    gate_y = col_bottom + 18
    parts.append(
        f'  <rect x="36" y="{gate_y:.0f}" width="1848" height="64" rx="18" fill="#FFFFFF" '
        f'stroke="#D1D5DB" stroke-dasharray="7 6"/>'
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 26:.0f}" text-anchor="middle" class="gate">'
        "Read-only: the bot never restarts, scales, or pushes</text>"
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 48:.0f}" text-anchor="middle" class="gate-sub">'
        "Path A (Red/Blue on k3s) may reset faults. The Grok bot only diagnoses and files issues.</text>"
    )

    card_y = gate_y + 80

    def card2(n: int, x: float, line1: str, line2: str) -> str:
        return f"""  <g transform="translate({x:.0f},{card_y:.0f})">
    <rect width="592" height="96" rx="14" fill="#FFF7ED" stroke="#FDBA74"/>
    <text x="24" y="40" class="card-n">{n}.</text>
    <text x="52" y="40" class="card-t">{line1}</text>
    <text x="52" y="68" class="card-t">{line2}</text>
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
