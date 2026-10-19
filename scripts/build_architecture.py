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
    "aws-vpc",
    "aws-subnet-public",
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
    </symbol>
    <symbol id="i-aws-sg" viewBox="0 0 40 40">
      <rect x="2.5" y="2.5" width="35" height="35" rx="6" fill="#FFF5F5"
            stroke="#DD344C" stroke-width="2.2" stroke-dasharray="5 3.5"/>
    </symbol>
    <symbol id="i-aws-igw" viewBox="0 0 40 40">
      <rect fill="#8C4FFF" width="40" height="40"/>
      <path fill="#FFFFFF"
            d="M8 22h24v2H8zm4-4h16v2H12zm-2 8h20v2H10zm10-16l8 6H12z"/>
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
    cap_svg = (
        f'    <text class="cap" y="58" text-anchor="middle">{cap}</text>\n'
        if cap
        else ""
    )
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <g transform="translate(0,-32) rotate(23)">
      <path d="{path}" fill="{GROK_RED}"/>
    </g>
    <g transform="translate(-12,-43)">
      <rect x="-8" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
      <rect x="1.2" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
    </g>
    <text class="name" y="36" text-anchor="middle">{name}</text>
{cap_svg}  </g>"""


def group(
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    icon: str | None = None,
    style: str | None = None,
) -> str:
    # AWS Architecture Icons group treatments (diagram-as-code / PowerPoint toolkit):
    # VPC = purple dashed #8C4FFF, public subnet = green #7AA116, default = gray card.
    palettes = {
        None: {
            "fill": "#F8FAFC",
            "stroke": "#E5E7EB",
            "sw": "1.5",
            "dash": "",
            "rx": "22",
            "cls": "group",
        },
        "vpc": {
            "fill": "#FFFFFF",
            "stroke": "#8C4FFF",
            "sw": "2.4",
            "dash": ' stroke-dasharray="7 5"',
            "rx": "6",
            "cls": "group-vpc",
        },
        "public_subnet": {
            "fill": "#F7FBEA",
            "stroke": "#7AA116",
            "sw": "2.2",
            "dash": "",
            "rx": "6",
            "cls": "group-subnet",
        },
    }
    pal = palettes[style]
    icon_svg = ""
    text_x = x + 24
    icon_size = 24 if style in {"vpc", "public_subnet"} else 22
    if icon:
        icon_svg = (
            f'  <use href="#i-{icon}" xlink:href="#i-{icon}" '
            f'x="{x + 12:.0f}" y="{y + 8:.0f}" width="{icon_size}" height="{icon_size}"/>\n'
        )
        text_x = x + 42
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="{pal["rx"]}" fill="{pal["fill"]}" stroke="{pal["stroke"]}" '
        f'stroke-width="{pal["sw"]}"{pal["dash"]}/>\n'
        f"{icon_svg}"
        f'  <text x="{text_x:.0f}" y="{y + 26:.0f}" class="{pal["cls"]}">{label}</text>'
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


def arc(
    x1: float,
    y1: float,
    cx: float,
    cy: float,
    x2: float,
    y2: float,
    dashed: bool = False,
) -> str:
    """One quadratic bezier — used for the PromQL query under the observability row."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    return (
        f'  <path d="M {x1:.0f},{y1:.0f} Q {cx:.0f},{cy:.0f} {x2:.0f},{y2:.0f}" '
        f'fill="none" class="arrow" stroke-linecap="round"{dash} marker-end="url(#arr)"/>'
    )


def satellite(x: float, y: float, icon: str, name: str, cap: str, size: float = 26) -> str:
    """Small icon with the name to its right — an attachment, not a chained node."""
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" x="{size / 2 + 8:.0f}" y="5" text-anchor="start" style="font-size:14px">{name}</text>
    <text class="cap" x="{size / 2 + 8:.0f}" y="22" text-anchor="start" style="font-size:13px">{cap}</text>
  </g>"""


def pill(x: float, y: float, text: str) -> str:
    w = max(56, 8.2 * len(text) + 22)
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
    W, H = 1920, 1200
    gy = 52
    main_h = 974
    col_bottom = gy + main_h  # 1026

    bot_x, bot_w = 1396, 504
    vpc_x, vpc_w = 16, 1364

    # AWS Architecture Icons groups: VPC (purple dashed) wraps the public subnet
    # (green) which holds the EC2 host. Terraform still has the one provision arrow.
    g_bot = group(bot_x, gy, bot_w, main_h, "Grok Bot  ·  local or AWS")
    g_vpc = group(
        vpc_x, gy, vpc_w, main_h, "VPC  sre-enterprise-vpc",
        icon="aws-vpc", style="vpc",
    )
    subnet_x, subnet_y = vpc_x + 8, gy + 36
    subnet_w, subnet_h = vpc_w - 16, main_h - 46
    g_subnet = group(
        subnet_x, subnet_y, subnet_w, subnet_h,
        "public_ingress  ·  one EC2 host",
        icon="aws-subnet-public", style="public_subnet",
    )
    ec2_x, ec2_w = vpc_x, vpc_w

    aws_icon = 48
    aws_r = gy + LABEL_BAND + aws_icon + 8  # 164
    tf_x, ec2_node_x = 400, 590
    # IAM / SSM satellites hang off the EC2 node (no arrows — Terraform creates
    # the role and profile; deploy_remote.py uses SSM).
    iam_x, ssm_x, sg_x, igw_x = 680, 860, 1048, 1238

    nested_y = aws_r + 70  # 234
    nested_h = col_bottom - nested_y - 14  # 746
    k3s_x, k3s_w = 32, 228
    lab_x = 308
    lab_w = ec2_x + ec2_w - 16 - lab_x  # 1056
    # Two alley spines. Red climbs inside k3s (left). Blue climbs in the
    # gutter (right). Horizontal segments never share an x with the other spine.
    alley_blue = 282
    alley_red = 220

    g_k3s = group(k3s_x, nested_y, k3s_w, nested_h, "k3s on this host")
    g_lab = group(lab_x, nested_y, lab_w, nested_h, "Compose lab on this host", icon="docker")

    r1 = 420  # Traffic / api-gw / order / payment (room above for Red flyover)
    r2 = 700  # Redis + Postgres under order-service; Red Team in k3s
    r3 = 840  # Prometheus → Alertmanager → incident-bridge; Blue Team
    graf_y = 978  # Grafana sits under Prometheus, not on the alert row

    k3s_cx = k3s_x + k3s_w / 2  # 146
    k3s_node_y = nested_y + LABEL_BAND + ICON + 10  # 360
    tg_x, gw_x, os_x, ps_x = 400, 580, 820, 1140
    rd_x, pg_x = os_x - 90, os_x + 90  # 730, 910 — short verticals only
    prom_x, am_x, br_x = gw_x, 860, 1140  # observability left → right
    graf_x = prom_x

    bot_cx = bot_x + bot_w / 2  # 1648
    bot_avatar_y = gy + 190
    bot_row_y = bot_avatar_y + 360
    gh_x, ping_x = bot_cx - 155, bot_cx + 155

    nodes = [
        node(tf_x, aws_r, "terraform", "Terraform", "optional AWS", size=aws_icon),
        node(ec2_node_x, aws_r, "aws-ec2", "EC2", "compose + k3s", size=aws_icon),
        satellite(iam_x, aws_r - aws_icon / 2 + 6, "aws-iam", "IAM", "role + profile"),
        satellite(ssm_x, aws_r - aws_icon / 2 + 6, "aws-ssm", "SSM", "deploy_remote.py"),
        satellite(sg_x, aws_r - aws_icon / 2 + 6, "aws-sg", "SG", "ingress + internal"),
        satellite(igw_x, aws_r - aws_icon / 2 + 6, "aws-igw", "IGW", "public RT only"),
        node(k3s_cx, k3s_node_y, "k3s", "k3s", "Agent sandbox"),
        node(k3s_cx, r2, "person-red", "Red Team", "Injects faults"),
        node(k3s_cx, r3, "person-blue", "Blue Team", "Detects and resets"),
        node(tg_x, r1, "traffic", "Traffic", "Live load"),
        node(gw_x, r1, "fastapi", "api-gw", "Gateway"),
        node(os_x, r1, "fastapi", "order-service", "Orders"),
        node(ps_x, r1, "fastapi", "payment-service", "Payments"),
        node(rd_x, r2, "redis", "Redis", "order-service cache"),
        node(pg_x, r2, "postgresql", "PostgreSQL", "orders_db"),
        node(prom_x, r3, "prometheus", "Prometheus", "Scrapes + rules"),
        node(am_x, r3, "alertmanager", "Alertmanager", "Groups alerts"),
        node(br_x, r3, "document", "incident-bridge", "PromQL · jsonl · k8s"),
        node(graf_x, graf_y, "grafana", "Grafana", ""),
        grok_avatar(bot_cx, bot_avatar_y, "AI Incident Diagnosis", ""),
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
      .group-vpc {{ font: 600 17px Arial, Helvetica, sans-serif; fill: #5B3BB4; }}
      .group-subnet {{ font: 600 17px Arial, Helvetica, sans-serif; fill: #5B7C10; }}
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
    parts.append(g_vpc)
    parts.append(g_subnet)
    parts.append(g_k3s)
    parts.append(g_lab)
    parts.append(g_bot)
    # Unused subnets live in the VPC but have no workloads today — caption only.
    parts.append(
        f'  <text x="{vpc_x + vpc_w - 14:.0f}" y="{gy + 26:.0f}" text-anchor="end" '
        f'class="cap">unused: app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24</text>'
    )
    parts.extend(nodes)

    svc_ic = _ic(r1)
    red_ic = _ic(r2)
    blue_ic = _ic(r3)
    aws_ic = aws_r - aws_icon / 2 - 4
    k3s_right = k3s_cx + 32
    db_top = _icon_top(r2)
    prom_top = _icon_top(r3)
    graf_top = _icon_top(graf_y)
    pay_y = nested_y + LABEL_BAND + 40  # 330, below Red ticks so they do not cross it
    # Red flies over the services (above the /api/payments U-turn) and ticks
    # down into order-service and payment-service. Blue stays in the corridor
    # under the captions and ticks up into order-service. The two never share y.
    red_y = nested_y + LABEL_BAND + 10  # 300
    svc_bottom = r1 + 52
    health_y = r1 + 100  # Blue horizontal under captions, above Redis/metrics
    metrics_from = r1 + 136

    # 1. Terraform → EC2 host. IAM and SSM are attached badges, not a chain.
    parts.append(arrow(tf_x + 40, aws_ic, ec2_node_x - 40, aws_ic))

    # 2–4. Request path. Pills sit in the gaps above the icons.
    parts.append(arrow(tg_x + 36, svc_ic, gw_x - 36, svc_ic))
    parts.append(arrow(gw_x + 36, svc_ic, os_x - 36, svc_ic))
    parts.append(arrow(os_x + 36, svc_ic, ps_x - 36, svc_ic))
    parts.append(pill((tg_x + gw_x) / 2, svc_ic - 20, "requests"))
    parts.append(pill((gw_x + os_x) / 2, svc_ic - 20, "/api/orders"))
    parts.append(pill((os_x + ps_x) / 2, svc_ic - 20, "POST /payments"))

    # 5. api-gw → payment-service proxy. U-turn above the icons, below the group label.
    parts.append(poly([
        (gw_x, _icon_top(r1) - 6),
        (gw_x, pay_y),
        (ps_x, pay_y),
        (ps_x, _icon_top(r1) - 6),
    ]))
    parts.append(pill((gw_x + os_x) / 2, pay_y - 16, "/api/payments"))

    # 6–7. order-service → Redis and PostgreSQL. Two short straight drops.
    # Drops start below the Red/Blue corridor; nothing else uses this column.
    parts.append(arrow(rd_x, metrics_from, rd_x, db_top))
    parts.append(arrow(pg_x, metrics_from, pg_x, db_top))

    # 8. Red Team → order-service and payment-service (not Traffic). Climbs
    # inside k3s (alley_red), flies over the service icons, then a short
    # bracket ticks down into both targets. Pill sits on that flyover.
    # Does not cross Blue's spine (Blue is below the row).
    red_tick_end = pay_y - 10  # stop above the /api/payments U-turn; no crossing
    parts.append(poly([
        (k3s_right, red_ic),
        (alley_red, red_ic),
        (alley_red, red_y),
        (ps_x - 18, red_y),
    ], marked=False))
    parts.append(arrow(os_x - 18, red_y, os_x - 18, red_tick_end))
    parts.append(arrow(ps_x - 18, red_y, ps_x - 18, red_tick_end))
    parts.append(pill((tg_x + gw_x) / 2, red_y, "faults"))

    # 9. Blue Team → FastAPI services (not Traffic). Climbs in the gutter
    # (alley_blue, right of Red's spine). Horizontal runs under api-gw to
    # order-service, then ticks up into the node.
    parts.append(poly([
        (k3s_right, blue_ic),
        (alley_blue, blue_ic),
        (alley_blue, health_y),
        (os_x + 18, health_y),
    ], marked=False))
    parts.append(arrow(os_x + 18, health_y, os_x + 18, svc_bottom))
    parts.append(pill((gw_x + os_x) / 2, health_y, "health ×3 / reset"))

    # 10. Blue Team → Prometheus (query). T-junction at alley_blue; does not
    # cross Red's spine. Stays under Redis/Postgres.
    parts.append(arrow(alley_blue, blue_ic, prom_x - 48, blue_ic))
    parts.append(pill(tg_x + 20, blue_ic - 20, "query"))

    # 11. Services → Prometheus. One vertical in the api-gw / Prometheus column.
    parts.append(arrow(gw_x, metrics_from, gw_x, prom_top))
    parts.append(pill(gw_x + 52, (metrics_from + prom_top) / 2, "3 scrape jobs"))

    # 12–13. Observability row, left → right, short straight arrows.
    parts.append(arrow(prom_x + 44, blue_ic, am_x - 44, blue_ic))
    parts.append(pill((prom_x + am_x) / 2, blue_ic - 20, "firing alerts"))
    parts.append(arrow(am_x + 44, blue_ic, br_x - 44, blue_ic))
    parts.append(pill((am_x + br_x) / 2, blue_ic - 20, "webhook"))

    # 14. Prometheus → Grafana, directly below. Pill sits left of the drop
    # so it does not sit on the PromQL arc.
    parts.append(arrow(prom_x, r3 + 52, prom_x, graf_top))
    parts.append(pill(prom_x - 50, (r3 + 52 + graf_top) / 2, "reads"))

    # 15. Bridge PromQL back to Prometheus: one shallow arc under the row.
    # Dip sits under Alertmanager (empty), arriving at Prometheus from the
    # right — not through Grafana, not along the canvas bottom.
    pq_y = r3 + 82
    parts.append(arc(br_x, r3 + 56, am_x, pq_y, prom_x + 52, r3 + 56, dashed=True))
    parts.append(pill(am_x, pq_y + 16, "PromQL"))

    # 16. Bridge → Grok avatar via the EC2/Grok gutter (orthogonal).
    hex_cy = bot_avatar_y - 32
    gutter = (ec2_x + ec2_w + bot_x) / 2  # 1388
    parts.append(poly([
        (br_x + 40, blue_ic),
        (gutter, blue_ic),
        (gutter, hex_cy),
        (bot_cx - 52, hex_cy),
    ]))
    parts.append(pill(gutter + 90, hex_cy - 18, "enriched JSON"))

    # 17–18. Grok → GitHub / owner ping: stem down, then orthogonal split.
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
        "AWS/EC2 is optional: docker compose up is the same lab. "
        "The bot only needs outbound HTTPS from the bridge.</text>"
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
