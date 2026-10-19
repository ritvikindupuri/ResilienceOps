#!/usr/bin/env python3
"""Build docs/architecture.svg in the Grok-bot-repo icon style.

Official marks live in docs/icons/ (AWS Architecture Icons, CNCF/k3s,
Grafana plugin Alertmanager, Simple Icons brand glyphs). Generic person /
clock / bell / document / traffic symbols are drawn here. The Grok bot
avatar is the real mark: a rounded hexagon tilted ~22°, fill #FB2B3E,
with two upright white capsule eyes.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "docs" / "icons"
OUT = ROOT / "docs" / "architecture.svg"

GROK_RED = "#FB2B3E"  # rgb(251, 43, 62) — actual bot fill

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
    cap_svg = (
        f'    <text class="cap" y="40" text-anchor="middle">{cap}</text>\n'
        if cap
        else ""
    )
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{top:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" y="18" text-anchor="middle">{name}</text>
{cap_svg}  </g>"""


def _rounded_hexagon_path(radius: float = 42, corner: float = 7) -> str:
    """Flat-top hexagon with quadratic corner rounding.

    Rotated ~22° in grok_avatar so a flat edge runs top-left to bottom-right.
    """
    verts = []
    for i in range(6):
        ang = math.radians(i * 60)  # vertex-east = flat top
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
    """Actual bot mark: rounded hexagon tilted ~22°, fill #FB2B3E, no outline.

    Two WHITE upright capsules (width:height ≈ 1:2.2), side by side, slightly
    left of and above center — they stay vertical and do not rotate with the hex.
    """
    path = _rounded_hexagon_path()
    # Capsules 6 x 13.2 → 1:2.2. Pair midpoint is left of and above hex center.
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <g transform="translate(0,-32) rotate(23)">
      <path d="{path}" fill="{GROK_RED}"/>
    </g>
    <g transform="translate(-12,-43)">
      <rect x="-8" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
      <rect x="1.2" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
    </g>
    <text class="name" y="36" text-anchor="middle">{name}</text>
    <text class="cap" y="58" text-anchor="middle">{cap}</text>
  </g>"""


def group(x: float, y: float, w: float, h: float, label: str, icon: str | None = None) -> str:
    icon_svg = ""
    text_x = x + 24
    if icon:
        icon_svg = (
            f'  <use href="#i-{icon}" xlink:href="#i-{icon}" '
            f'x="{x + 16:.0f}" y="{y + 10:.0f}" width="22" height="22"/>\n'
        )
        text_x = x + 44
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="22" fill="#F8FAFC" stroke="#E5E7EB"/>\n'
        f"{icon_svg}"
        f'  <text x="{text_x:.0f}" y="{y + 28:.0f}" class="group">{label}</text>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    return (
        f'  <line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
        f'class="arrow"{dash} marker-end="url(#arr)"/>'
    )


def poly(points: list[tuple[float, float]], dashed: bool = False, marked: bool = True) -> str:
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in points)
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    end = ' marker-end="url(#arr)"' if marked else ""
    return (
        f'  <polyline points="{pts}" fill="none" class="arrow" '
        f'stroke-linejoin="round" stroke-linecap="round"{dash}{end}/>'
    )


def pill(x: float, y: float, text: str) -> str:
    w = max(92, 8.4 * len(text) + 24)
    return f"""  <g transform="translate({x - w / 2:.1f},{y - 11:.0f})">
    <rect width="{w:.1f}" height="22" rx="11" fill="#FFFFFF" stroke="#D1D5DB"/>
    <text x="{w / 2:.1f}" y="16" text-anchor="middle" class="pill">{text}</text>
  </g>"""


def _ic(node_y: float) -> float:
    """Vertical center of a node icon (node y is the name baseline)."""
    return node_y - ICON / 2 - 4


def _icon_top(node_y: float) -> float:
    return node_y - ICON - 8


def build() -> str:
    W, H = 1920, 1100
    gy = 52
    main_h = 856
    col_bottom = gy + main_h  # 908

    bot_x, bot_w = 1396, 504
    ec2_x, ec2_w = 16, 1364

    g_bot = group(bot_x, gy, bot_w, main_h, "Your Grok bot")
    g_ec2 = group(ec2_x, gy, ec2_w, main_h, "EC2 host", icon="aws-ec2")

    # AWS control-plane row sits above Compose (not above k3s) so captions
    # cannot collide with the k3s group label.
    aws_icon = 48
    aws_r = gy + LABEL_BAND + aws_icon + 6  # 162
    tf_x, iam_x, ssm_x = 520, 720, 930

    nested_y = aws_r + 58  # 220
    nested_h = col_bottom - nested_y - 14  # 674
    k3s_x, k3s_w = 32, 228
    lab_x = 308
    lab_w = ec2_x + ec2_w - 16 - lab_x  # 1056
    alley_blue = 272  # vertical corridor between k3s and compose
    alley_red = 294

    g_k3s = group(k3s_x, nested_y, k3s_w, nested_h, "k3s sandbox")
    g_lab = group(lab_x, nested_y, lab_w, nested_h, "Compose lab", icon="docker")

    # Rows: services, data stores, observability. Corridors between them
    # hold orthogonal rails so arrows never run through nodes.
    r1 = nested_y + LABEL_BAND + ICON + 50  # 394  (band above icons for /api/payments)
    r2 = r1 + 300  # 694  Redis / Postgres / Red
    r3 = r2 + 124  # 818  Prom / Grafana / AM / bridge / Blue

    k3s_cx = k3s_x + k3s_w / 2  # 146
    tg_x, gw_x, os_x, ps_x = 380, 560, 840, 1180
    rd_x, pg_x = 700, 1000
    # Grafana sits between Prom and AM on the same row but is NOT on the alert path.
    prom_x, graf_x, am_x, br_x = gw_x, 760, 1000, 1220

    bot_cx = bot_x + bot_w / 2  # 1648
    bot_avatar_y = gy + 190
    bot_row_y = bot_avatar_y + 360
    gh_x, ping_x = bot_cx - 155, bot_cx + 155

    nodes = [
        node(tf_x, aws_r, "terraform", "Terraform", "provisions host", size=aws_icon),
        node(iam_x, aws_r, "aws-iam", "IAM", "role + profile", size=aws_icon),
        node(ssm_x, aws_r, "aws-ssm", "SSM", "deploy_remote.py", size=aws_icon),
        node(k3s_cx, r1, "k3s", "k3s", "Agent sandbox"),
        node(k3s_cx, r2, "person-red", "Red Team", "Injects faults"),
        node(k3s_cx, r3, "person-blue", "Blue Team", "Detects and resets"),
        node(tg_x, r1, "traffic", "Traffic", "Live load"),
        node(gw_x, r1, "fastapi", "api-gw", "Gateway"),
        node(os_x, r1, "fastapi", "order-service", "Orders"),
        node(ps_x, r1, "fastapi", "payment-service", "Payments"),
        node(rd_x, r2, "redis", "Redis", "order-service cache"),
        node(pg_x, r2, "postgresql", "PostgreSQL", "orders_db"),
        node(prom_x, r3, "prometheus", "Prometheus", "Scrapes + rules"),
        node(graf_x, r3, "grafana", "Grafana", ""),
        node(am_x, r3, "alertmanager", "Alertmanager", "Groups alerts"),
        node(br_x, r3, "document", "incident-bridge", "PromQL · jsonl · k8s"),
        grok_avatar(bot_cx, bot_avatar_y, "AI Incident Diagnosis", "Your Grok bot"),
        node(gh_x, bot_row_y, "github", "GitHub issue", "label: incident"),
        node(ping_x, bot_row_y, "bell", "Owner ping", "Firing critical"),
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
      .pill {{ font: 600 12px Arial, Helvetica, sans-serif; fill: #4B5563; }}
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
  <text x="{W / 2:.0f}" y="40" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
'''
    ]
    parts.append(g_ec2)
    parts.append(g_k3s)
    parts.append(g_lab)
    parts.append(g_bot)
    parts.extend(nodes)

    svc_ic = _ic(r1)
    red_ic = _ic(r2)
    blue_ic = _ic(r3)
    aws_ic = aws_r - aws_icon / 2 - 4
    k3s_right = k3s_cx + 32
    # Stop below-node ticks under the caption box so arrows never cross labels.
    svc_label_clear = r1 + 54
    db_top = _icon_top(r2)
    prom_top = _icon_top(r3)
    pay_y = nested_y + LABEL_BAND + 18  # 294, between Compose label and service icons
    health_y = r1 + 80   # below service captions (~434)
    fault_y = r1 + 128
    metrics_y = r1 + 176
    db_rail_y = r1 + 214  # just above Redis icon tops (~r2-76)
    db_drop_x = (os_x + 80 + ps_x - 80) / 2  # order↔payment gap, rails break around this x
    pq_y = r3 + 88

    # Terraform → IAM role/instance profile → SSM (deploy_remote.py).
    parts.append(arrow(tf_x + 36, aws_ic, iam_x - 36, aws_ic))
    parts.append(arrow(iam_x + 36, aws_ic, ssm_x - 36, aws_ic))

    # Request path (icon-center row). Pills sit in the gaps between icons.
    parts.append(arrow(tg_x + 36, svc_ic, gw_x - 36, svc_ic))
    parts.append(arrow(gw_x + 36, svc_ic, os_x - 36, svc_ic))
    parts.append(arrow(os_x + 36, svc_ic, ps_x - 36, svc_ic))
    parts.append(pill((tg_x + gw_x) / 2, svc_ic - 20, "requests"))
    parts.append(pill((gw_x + os_x) / 2, svc_ic - 20, "/api/orders"))
    parts.append(pill((os_x + ps_x) / 2, svc_ic - 20, "POST /payments"))

    # api-gw → payment /api/payments: U-turn above the icons, below the group label.
    parts.append(poly([
        (gw_x, _icon_top(r1) - 6),
        (gw_x, pay_y),
        (ps_x, pay_y),
        (ps_x, _icon_top(r1) - 6),
    ]))
    parts.append(pill((gw_x + os_x) / 2, pay_y - 16, "/api/payments"))

    # Blue GET /health + POST /fault/reset. Spine in the k3s↔compose alley.
    # Rails break around db_drop_x so the DB vertical does not cross them.
    parts.append(poly([(k3s_right, blue_ic), (alley_blue, blue_ic), (alley_blue, health_y)], marked=False))
    parts.append(poly([(alley_blue, health_y), (db_drop_x - 20, health_y)], marked=False))
    parts.append(poly([(db_drop_x + 20, health_y), (ps_x - 16, health_y)], marked=False))
    parts.append(arrow(gw_x, health_y, gw_x, svc_label_clear))
    parts.append(arrow(os_x - 16, health_y, os_x - 16, svc_label_clear))
    parts.append(arrow(ps_x - 16, health_y, ps_x - 16, svc_label_clear))
    parts.append(pill((gw_x + os_x) / 2 - 20, health_y + 16, "GET /health · reset"))

    # Red: order-service POST /fault/* and payment-service tc netem.
    parts.append(poly([
        (k3s_right, red_ic),
        (alley_red, red_ic),
        (alley_red, fault_y),
        (db_drop_x - 20, fault_y),
    ], marked=False))
    parts.append(poly([(db_drop_x + 20, fault_y), (ps_x + 16, fault_y)], marked=False))
    parts.append(arrow(os_x + 16, fault_y, os_x + 16, svc_label_clear))
    parts.append(arrow(ps_x + 16, fault_y, ps_x + 16, svc_label_clear))
    parts.append(pill((gw_x + os_x) / 2 - 20, fault_y + 16, "POST /fault/*"))
    parts.append(pill(ps_x - 100, fault_y + 16, "tc netem"))

    # Metrics bracket above Redis (no ticks through the health/fault rails),
    # then a vertical in the api-gw column into Prometheus.
    parts.append(poly([(gw_x, metrics_y), (os_x + 24, metrics_y)], marked=False))
    parts.append(arrow(gw_x, metrics_y, gw_x, prom_top))
    parts.append(pill(gw_x - 56, (metrics_y + prom_top) / 2, "metrics"))

    # order-service → Redis / Postgres. Drop in the rail gap (order↔payment).
    parts.append(poly([
        (os_x + 40, r1 + 56),
        (db_drop_x, r1 + 56),
        (db_drop_x, db_rail_y),
        (rd_x, db_rail_y),
        (rd_x, db_top),
    ]))
    parts.append(poly([
        (db_drop_x, db_rail_y),
        (pg_x, db_rail_y),
        (pg_x, db_top),
    ]))

    # Prometheus → Grafana (reads). Short hop; Grafana is not on the alert path.
    parts.append(arrow(prom_x + 40, blue_ic, graf_x - 40, blue_ic))
    parts.append(pill((prom_x + graf_x) / 2, blue_ic + 20, "reads"))
    # Prometheus → Alertmanager → bridge. U-turn under Grafana so the alert
    # line does not run through the Grafana icon.
    fire_y = r3 + 50
    # U-turn under Grafana, then into AM from the left at icon-center (x is
    # left of the "Groups alerts" caption).
    parts.append(poly([
        (prom_x, r3 + 52),
        (prom_x, fire_y),
        (am_x - 70, fire_y),
        (am_x - 70, blue_ic),
        (am_x - 40, blue_ic),
    ]))
    parts.append(arrow(am_x + 40, blue_ic, br_x - 40, blue_ic))
    parts.append(pill((graf_x + am_x) / 2 + 20, fire_y + 16, "firing alerts"))

    # Bridge PromQL: dashed U under the firing rail, arrowhead below the
    # Prometheus caption so the line does not run through "Scrapes + rules".
    parts.append(poly([
        (br_x, r3 + 52),
        (br_x, pq_y),
        (prom_x - 36, pq_y),
        (prom_x - 36, r3 + 52),
    ], dashed=True))
    parts.append(pill((am_x + br_x) / 2, pq_y - 16, "PromQL"))

    # Blue instant query → Prometheus (gutter, then into Prometheus).
    parts.append(poly([
        (k3s_right, blue_ic),
        (alley_blue, blue_ic),
        (prom_x - 40, blue_ic),
    ], dashed=True))
    parts.append(pill((k3s_right + alley_blue + prom_x - 40) / 3 + 40, blue_ic + 20, "query"))

    # Bridge → Grok avatar via the EC2/Grok gutter (orthogonal).
    hex_cy = bot_avatar_y - 32
    gutter = (ec2_x + ec2_w + bot_x) / 2  # 1388
    parts.append(poly([
        (br_x + 40, blue_ic),
        (gutter, blue_ic),
        (gutter, hex_cy),
        (bot_cx - 52, hex_cy),
    ]))
    parts.append(pill(gutter + 90, hex_cy - 18, "enriched JSON"))

    # Grok → GitHub / owner ping: stem down, then orthogonal split.
    out_y = bot_avatar_y + 78
    fork_y = out_y + 36
    gh_top = _icon_top(bot_row_y)
    parts.append(poly([(bot_cx, out_y), (bot_cx, fork_y)], marked=False))
    parts.append(poly([(bot_cx, fork_y), (gh_x, fork_y), (gh_x, gh_top)]))
    parts.append(poly([(bot_cx, fork_y), (ping_x, fork_y), (ping_x, gh_top)]))
    parts.append(pill(bot_cx, fork_y - 16, "read-only"))

    gate_y = col_bottom + 10
    parts.append(
        f'  <rect x="16" y="{gate_y:.0f}" width="1888" height="56" rx="18" fill="#FFFFFF" '
        f'stroke="#D1D5DB" stroke-dasharray="7 6"/>'
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 22:.0f}" text-anchor="middle" class="gate">'
        "Read-only: the bot never restarts, scales, or pushes</text>"
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 44:.0f}" text-anchor="middle" class="gate-sub">'
        "Path A (Red/Blue on k3s) may reset faults. The Grok bot only diagnoses and files issues. "
        "Compose + k3s run on the EC2 host.</text>"
    )

    card_y = gate_y + 68

    def card2(n: int, x: float, line1: str, line2: str) -> str:
        return f"""  <g transform="translate({x:.0f},{card_y:.0f})">
    <rect width="592" height="96" rx="14" fill="#FFF7ED" stroke="#FDBA74"/>
    <text x="24" y="40" class="card-n">{n}.</text>
    <text x="52" y="40" class="card-t">{line1}</text>
    <text x="52" y="68" class="card-t">{line2}</text>
  </g>"""

    parts.append(card2(1, 16, "Fault or real outage trips a", "Prometheus alert rule."))
    parts.append(card2(2, 664, "Bridge adds evidence and posts", "enriched JSON to your bot."))
    parts.append(card2(3, 1312, "Bot diagnoses and files or", "updates a GitHub issue."))

    parts.append("</svg>\n")
    return "\n".join(parts)


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
