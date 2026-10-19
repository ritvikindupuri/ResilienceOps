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
    "aws-s3",
    "aws-cloudwatch",
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


def node(x: float, y: float, icon: str, name: str, cap: str, size: float = ICON, cap2: str = "") -> str:
    # Icon sits above the name; caller must place y so the icon stays below the group label.
    top = -size - 8
    cap_svg = (
        f'    <text class="cap" y="40" text-anchor="middle">{cap}</text>\n'
        if cap
        else ""
    )
    if cap2:
        cap_svg += (
            f'    <text class="cap" y="56" text-anchor="middle">{cap2}</text>\n'
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
        "account": {
            "fill": "#F8FAFC",
            "stroke": "#94A3B8",
            "sw": "1.6",
            "dash": "",
            "rx": "8",
            "cls": "group",
        },
        "sg": {
            "fill": "none",
            "stroke": "#DD344C",
            "sw": "2.0",
            "dash": ' stroke-dasharray="5 3.5"',
            "rx": "8",
            "cls": "group-sg",
        },
        "optional": {
            "fill": "#FAFBFC",
            "stroke": "#94A3B8",
            "sw": "1.6",
            "dash": ' stroke-dasharray="5 4"',
            "rx": "8",
            "cls": "group",
        },
    }
    pal = palettes[style]
    icon_svg = ""
    text_x = x + 24
    icon_size = 24 if style in {"vpc", "public_subnet", "sg"} else 22
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


def satellite(
    x: float,
    y: float,
    icon: str,
    name: str,
    cap: str,
    size: float = 26,
    label_side: str = "right",
    name_size: int = 14,
) -> str:
    """Small icon with the name beside or below it — an attachment, not a chained node."""
    if label_side == "below":
        return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" y="{size / 2 + 16:.0f}" text-anchor="middle"
          style="font:700 {name_size}px Arial, Helvetica, sans-serif">{name}</text>
    <text class="cap" y="{size / 2 + 32:.0f}" text-anchor="middle"
          style="font:13px Arial, Helvetica, sans-serif">{cap}</text>
  </g>"""
    if label_side == "left":
        tx, anchor = -(size / 2 + 10), "end"
    else:
        tx, anchor = size / 2 + 14, "start"
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" x="{tx:.0f}" y="5" text-anchor="{anchor}" style="font-size:14px">{name}</text>
    <text class="cap" x="{tx:.0f}" y="22" text-anchor="{anchor}" style="font-size:13px">{cap}</text>
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

    # Title band is 0–58 (36px type, baseline y=34). Nothing else may enter
    # that band — the AWS-account strip starts below it. IGW straddles the
    # VPC *right* border; labels sit in the VPC–Grok gutter, off the stroke.
    aws_icon = 44
    tf_x, deploy_x, op_y = 84, 268, 118  # icon top = 66, fully below the title
    # Wider account strip so S3 / Param Store / SSM / IAM / CW sit in one row.
    acct_x, acct_y, acct_w, acct_h = 430, 60, 1000, 108  # 60–168, under the title
    # S3+SSM sit together so deploy_remote.py can fork without crossing Param.
    # put_lab_secrets.py sits immediately left of Param Store.
    s3_x, ssm_x, secrets_x, param_x, iam_x, cw_x = 540, 670, 860, 1040, 1180, 1320
    acct_node_y = 108  # icons; labels sit below inside the strip

    # VPC is 8px shorter than 896 so the footer box can sit *below* the
    # purple stroke with padding, instead of kissing the VPC border.
    vpc_x, vpc_y, vpc_w, vpc_h = 16, 176, 1276, 888  # right 1292, bottom 1064
    bot_x, bot_y, bot_w, bot_h = 1452, 176, 452, 888  # gutter 160px for IGW labels
    col_bottom = vpc_y + vpc_h

    g_bot = group(bot_x, bot_y, bot_w, bot_h, "Grok Bot (external)")
    g_vpc = group(
        vpc_x, vpc_y, vpc_w, vpc_h, "VPC  sre-enterprise-vpc",
        icon="aws-vpc", style="vpc",
    )
    g_acct = group(
        acct_x, acct_y, acct_w, acct_h,
        "AWS account",
        style="account",
    )

    # Green public subnet fills the VPC except a slim right gutter (IGW labels
    # live *outside* the purple border, in the VPC–Grok gap).
    subnet_x, subnet_y = vpc_x + 10, vpc_y + 36
    subnet_w, subnet_h = vpc_w - 24, vpc_h - 48
    g_subnet = group(
        subnet_x, subnet_y, subnet_w, subnet_h,
        "public_ingress  10.0.1.0/24  ·  one EC2 host",
        icon="aws-subnet-public", style="public_subnet",
    )

    # Dashed SG around the host contents (k3s + Compose), not around the VPC.
    sg_x, sg_y = subnet_x + 10, subnet_y + 34
    sg_w, sg_h = subnet_w - 20, subnet_h - 46
    g_sg = group(
        sg_x, sg_y, sg_w, sg_h,
        "SG  ingress + internal",
        icon="aws-sg", style="sg",
    )

    # SG title baseline is sg_y+26. k3s top needs a real gap under that type
    # (previously nested_y = sg_y+28 sat on the glyphs).
    nested_y = sg_y + 52
    k3s_x, k3s_w, k3s_opt_h = sg_x + 12, 248, 58
    g_k3s_opt = group(
        k3s_x, nested_y, k3s_w, k3s_opt_h,
        "k3s (optional)",
        icon="k3s", style="optional",
    )

    # Outer Compose wraps Agents *and* the app stack. k3s stays outside it
    # (deploy_k8s_sandbox.py is not a Compose service).
    compose_x = sg_x + 12
    compose_y = nested_y + k3s_opt_h + 12
    compose_w = sg_w - 24
    compose_h = sg_y + sg_h - compose_y - 10
    g_compose = group(
        compose_x, compose_y, compose_w, compose_h,
        "Docker Compose on this host",
        icon="docker",
    )

    inner_y = compose_y + 40
    inner_h = compose_y + compose_h - inner_y - 10
    agents_x, agents_w = compose_x + 10, 268
    app_x = agents_x + agents_w + 72
    app_w = compose_x + compose_w - 12 - app_x
    g_agents = group(
        agents_x, inner_y, agents_w, inner_h,
        "Agents (--profile agents)",
    )
    g_app = group(
        app_x, inner_y, app_w, inner_h,
        "App + observability (default)",
    )

    # Three alley spines in the Agents↔App gutter (never through box titles).
    # Red climbs (left). Scrape drops (middle). Blue climbs (right).
    alley_red = agents_x + agents_w + 16
    alley_scrape = agents_x + agents_w + 36
    alley_blue = app_x - 16

    r1 = inner_y + 176  # Traffic / api-gw / order / payment (room above for Red flyover)
    r2 = r1 + 152  # Redis + Postgres under order-service; Red Team in Agents
    r3 = r2 + 168  # Prometheus → Alertmanager → incident-bridge; Blue Team
    graf_y = inner_y + inner_h - 22  # keep Grafana name above the App stroke

    k3s_cx = agents_x + agents_w / 2
    # Keep payment-service / incident-bridge names inside the App stroke.
    tg_x, gw_x, os_x, ps_x = app_x + 64, app_x + 230, app_x + 450, app_x + 720
    rd_x, pg_x = os_x - 90, os_x + 90
    prom_x, am_x, br_x = gw_x, os_x + 40, ps_x
    graf_x = prom_x

    # IGW icon sits on the VPC right border (straddles the stroke). Labels
    # hang to the right, fully in the gutter — not on the dashed line.
    igw_x, igw_y = vpc_x + vpc_w, vpc_y + 56

    bot_cx = bot_x + bot_w / 2
    bot_avatar_y = bot_y + 160
    bot_row_y = bot_avatar_y + 360
    gh_x, ping_x = bot_cx - 155, bot_cx + 155

    nodes = [
        node(tf_x, op_y, "terraform", "Terraform", "optional AWS", size=aws_icon),
        node(deploy_x, op_y, "document", "deploy_remote.py", "operator", size=aws_icon),
        satellite(s3_x, acct_node_y, "aws-s3", "S3", "deploy → host", size=26, label_side="below"),
        satellite(ssm_x, acct_node_y, "aws-ssm", "SSM", "send_command", size=26, label_side="below"),
        satellite(secrets_x, acct_node_y, "document", "put_lab_secrets.py", "laptop → Param", size=26, label_side="below", name_size=11),
        satellite(param_x, acct_node_y, "aws-ssm", "Param Store", "secrets → .env", size=26, label_side="below"),
        satellite(iam_x, acct_node_y, "aws-iam", "IAM", "role + profile", size=26, label_side="below"),
        satellite(cw_x, acct_node_y, "aws-cloudwatch", "CW Logs", "agents → CW", size=26, label_side="below"),
        satellite(igw_x, igw_y, "aws-igw", "IGW", "public RT only", size=28, label_side="right"),
        node(k3s_cx, r2, "person-red", "Red Team", "Injects faults"),
        node(k3s_cx, r3, "person-blue", "Blue Team", "Detects and resets"),
        node(tg_x, r1, "traffic", "Traffic", "Live load"),
        node(gw_x, r1, "fastapi", "api-gw", "Gateway"),
        node(os_x, r1, "fastapi", "order-service", "Orders"),
        node(ps_x, r1, "fastapi", "payment-service", "Payments"),
        node(rd_x, r2, "redis", "Redis", "order-service cache"),
        node(pg_x, r2, "postgresql", "PostgreSQL", "orders_db"),
        node(prom_x, r3, "prometheus", "Prometheus", ""),
        node(am_x, r3, "alertmanager", "Alertmanager", "Groups alerts"),
        node(br_x, r3, "document", "incident-bridge", "PromQL · agent jsonl", cap2="(Compose agents)"),
        node(graf_x, graf_y, "grafana", "Grafana", "", size=52),
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
      .group-sg {{ font: 600 15px Arial, Helvetica, sans-serif; fill: #9B1C2E; }}
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
  <text x="{W / 2:.0f}" y="34" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
'''
    ]
    parts.append(g_acct)
    parts.append(g_vpc)
    parts.append(g_subnet)
    parts.append(g_sg)
    parts.append(g_k3s_opt)
    parts.append(g_compose)
    parts.append(g_agents)
    parts.append(g_app)
    parts.append(g_bot)
    # Operator reaches Grafana :3000 and api-gw :8000 through IGW + ingress SG.
    # Caption lives in the VPC–Grok gutter (same side as IGW labels) so it
    # does not cross Compose arrows.
    parts.append(
        f'  <text x="{igw_x + 20:.0f}" y="{igw_y + 52:.0f}" class="cap">'
        "operator :3000 / :8000</text>"
    )
    # Subtitles that do not fit in the group title band.
    parts.append(
        f'  <text x="{k3s_x + 42:.0f}" y="{nested_y + 44:.0f}" class="cap">'
        "deploy_k8s_sandbox.py</text>"
    )
    # Unused subnets live in the VPC but have no workloads today. Right of the
    # VPC title, *above* public_ingress. Account-strip drops stop at the VPC
    # stroke so they cannot run through this type.
    parts.append(
        f'  <text x="{vpc_x + vpc_w - 18:.0f}" y="{vpc_y + 26:.0f}" text-anchor="end" '
        f'class="cap">app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24 · unused</text>'
    )
    parts.extend(nodes)

    svc_ic = _ic(r1)
    red_ic = _ic(r2)
    blue_ic = _ic(r3)
    op_ic = op_y - aws_icon / 2 - 4
    k3s_right = k3s_cx + 44  # past the 68px person icon so shafts never clip Red/Blue
    db_top = _icon_top(r2)
    prom_top = _icon_top(r3)
    graf_top = graf_y - 52 - 8  # Grafana is drawn at size 52, not ICON
    pay_y = inner_y + 82
    # Red flies over the services (above the /api/payments U-turn) and ticks
    # down into order-service and payment-service. Blue's health bus sits
    # *below* Redis/Postgres so those arrows can start at order-service.
    red_y = inner_y + 58
    # Health ticks stop *below* the scrape collector so the two never share a
    # y in the service columns (a full-height tick would cross the merge bar).
    collector_y = r1 + 54  # under Gateway / Orders / Payments captions (below descenders)
    svc_bottom = r1 + 66  # health-tick arrowheads; 18px below the scrape bar
    health_y = r2 + 72  # well below Redis/Postgres captions (pills sit under the bus)

    # 1. Terraform (operator laptop, outside AWS) → VPC border, *right of*
    # the "VPC  sre-enterprise-vpc" title so the shaft never bisects the type.
    # Run the elbow just above the VPC stroke (not up at the "operator" cap).
    vpc_label_right = vpc_x + 250  # icon + "VPC  sre-enterprise-vpc"
    tf_land_x = max(vpc_label_right + 24, 400)
    tf_run_y = vpc_y - 5
    parts.append(poly([
        (tf_x, op_y + 52),
        (tf_x, tf_run_y),
        (tf_land_x, tf_run_y),
        (tf_land_x, vpc_y),
    ]))

    # 1b. deploy_remote.py → S3 → host and deploy_remote.py → SSM → host.
    # S3 is a short diagonal (nothing sits between deploy_remote.py and S3).
    # SSM uses an orthogonal under-caption highway so the shaft cannot run
    # through the S3 icon. Drops are vertical and stop at public_ingress.
    deploy_label_right = deploy_x + 110  # 18px bold "deploy_remote.py" ~160px wide
    fork_x = deploy_label_right + 16
    parts.append(arrow(fork_x, op_y, s3_x - 36, acct_node_y))
    ssm_run_y = acct_y + acct_h - 10  # 158: below satellite captions, above VPC
    vpc_top = vpc_y  # stop on the VPC stroke; unused-CIDR type sits below it
    parts.append(poly([
        (fork_x, op_y + 8),
        (fork_x, ssm_run_y),
        (ssm_x, ssm_run_y),
        (ssm_x, acct_node_y + 16),
    ]))
    parts.append(poly([(ssm_x, ssm_run_y), (ssm_x, vpc_top)]))
    drop_from = acct_node_y + 46  # below satellite captions, still in the strip
    parts.append(poly([(s3_x, drop_from), (s3_x, vpc_top)]))
    # 1c. put_lab_secrets.py → Param Store → host .env. Short hop between
    # the two icons (names sit below), then a vertical drop.
    parts.append(arrow(secrets_x + 16, acct_node_y, param_x - 16, acct_node_y))
    parts.append(poly([(param_x, drop_from), (param_x, vpc_top)]))

    # 2–4. Request path. Pills sit in the gaps above the icons.
    parts.append(arrow(tg_x + 36, svc_ic, gw_x - 36, svc_ic))
    parts.append(arrow(gw_x + 36, svc_ic, os_x - 36, svc_ic))
    parts.append(arrow(os_x + 36, svc_ic, ps_x - 36, svc_ic))
    parts.append(pill((tg_x + gw_x) / 2, svc_ic - 26, "requests"))
    parts.append(pill((gw_x + os_x) / 2, svc_ic - 26, "/api/orders"))
    parts.append(pill((os_x + ps_x) / 2, svc_ic - 26, "POST /payments"))

    # 5. api-gw → payment-service proxy. U-turn above the icons, below the group label.
    parts.append(poly([
        (gw_x, _icon_top(r1) - 6),
        (gw_x, pay_y),
        (ps_x, pay_y),
        (ps_x, _icon_top(r1) - 6),
    ]))
    parts.append(pill((gw_x + os_x) / 2, pay_y - 24, "/api/payments"))

    # 6–7. order-service → Redis and PostgreSQL. Fork just below the
    # order-service caption, then drop into each datastore. Stays above
    # the Blue health bus (no crossing).
    os_fork_y = r1 + 56
    parts.append(poly([
        (os_x - 10, os_fork_y),
        (rd_x, os_fork_y),
        (rd_x, db_top),
    ]))
    parts.append(poly([
        (os_x + 10, os_fork_y),
        (pg_x, os_fork_y),
        (pg_x, db_top),
    ]))

    # 8. Red Team → order-service and payment-service (not Traffic). Climbs
    # in the Agents↔App gutter (alley_red, *outside* the Agents title), flies
    # over the service icons, then a short bracket ticks down into both
    # targets. Pill sits *above* the flyover, between the ticks — not on the
    # shaft and not under the App title. Does not cross Blue's spine.
    red_tick_end = pay_y - 10  # stop above the /api/payments U-turn; no crossing
    parts.append(poly([
        (k3s_right, red_ic),
        (alley_red, red_ic),
        (alley_red, red_y),
        (ps_x - 18, red_y),
    ], marked=False))
    parts.append(arrow(os_x - 18, red_y, os_x - 18, red_tick_end))
    parts.append(arrow(ps_x - 18, red_y, ps_x - 18, red_tick_end))
    # Sit between the two ticks, above the flyover — not under the App title
    # and not on the shaft.
    parts.append(pill((os_x + ps_x) / 2, red_y - 26, "faults"))

    # 9. Blue Team health-checks api-gw, order-service, and payment-service
    # (monitor.py GET /health ×3). Reset POSTs /fault/reset on order-service
    # and payment-service only (fault_catalog.py). Three ticks; two pills.
    parts.append(poly([
        (k3s_right, blue_ic),
        (alley_blue, blue_ic),
        (alley_blue, health_y),
        (ps_x + 18, health_y),
    ], marked=False))
    parts.append(arrow(gw_x + 18, health_y, gw_x + 18, svc_bottom))
    parts.append(arrow(os_x + 18, health_y, os_x + 18, svc_bottom))
    parts.append(arrow(ps_x + 18, health_y, ps_x + 18, svc_bottom))
    # Sit on the health bus, clear of the observability-row pills (alerts / webhook).
    parts.append(pill(gw_x - 110, health_y, "health ×3"))
    parts.append(pill(ps_x - 50, health_y, "reset ×2"))

    # 10. Blue Team → Prometheus (query). T-junction at alley_blue; does not
    # cross Red's spine. Stays under Redis/Postgres.
    parts.append(arrow(alley_blue, blue_ic, prom_x - 48, blue_ic))
    parts.append(pill(tg_x + 20, blue_ic, "query"))

    # 11. Services → Prometheus. A merge bar sits *under the three service
    # captions* (above Redis and above the Blue health ticks), drops the
    # Agents↔App gutter (alley_scrape), and enters Prometheus from the left.
    # Separate x from Blue's spine; separate y from the health bus.
    parts.append(poly([
        (ps_x, collector_y),
        (alley_scrape, collector_y),
        (alley_scrape, prom_top + 8),
        (prom_x - 48, prom_top + 8),
    ]))
    # Below the collector in the Traffic / api-gw gap — not on "Live load", Redis, or the health bus.
    parts.append(pill((tg_x + gw_x) / 2, collector_y + 20, "3 scrape jobs"))

    # 12–13. Observability row, left → right, short straight arrows.
    parts.append(arrow(prom_x + 44, blue_ic, am_x - 44, blue_ic))
    parts.append(pill((prom_x + am_x) / 2, blue_ic - 28, "alerts"))
    parts.append(arrow(am_x + 44, blue_ic, br_x - 44, blue_ic))
    parts.append(pill((am_x + br_x) / 2, blue_ic - 28, "webhook"))

    # 14. Prometheus → Grafana, directly below. Pill sits left of the drop
    # so it does not sit on the PromQL arc.
    parts.append(arrow(prom_x, r3 + 24, prom_x, graf_top))
    parts.append(pill(prom_x - 100, (r3 + 24 + graf_top) / 2, "reads"))

    # 15. Bridge PromQL back to Prometheus. Dip under Alertmanager's caption
    # (empty), arrive at Prometheus from the right, above Grafana.
    parts.append(arc(br_x, r3 + 58, am_x, r3 + 92, prom_x + 72, r3 + 16, dashed=True))
    parts.append(pill(am_x + 50, r3 + 104, "PromQL"))

    # 16. Bridge → Grok avatar via the EC2/Grok gutter (orthogonal).
    hex_cy = bot_avatar_y - 32
    gutter = (vpc_x + vpc_w + bot_x) / 2  # 1388
    parts.append(poly([
        (br_x + 40, blue_ic),
        (gutter, blue_ic),
        (gutter, hex_cy),
        (bot_cx - 52, hex_cy),
    ]))
    # Fully inside the Grok card, above the incoming shaft — not on the left edge.
    parts.append(pill(bot_cx - 130, hex_cy - 32, "enriched JSON"))

    # 17–18. Grok → GitHub / owner ping: stem down, then orthogonal split.
    out_y = bot_avatar_y + 78
    fork_y = out_y + 36
    gh_top = _icon_top(bot_row_y)
    parts.append(poly([(bot_cx, out_y), (bot_cx, fork_y)], marked=False))
    parts.append(poly([(bot_cx, fork_y), (gh_x, fork_y), (gh_x, gh_top)]))
    parts.append(poly([(bot_cx, fork_y), (ping_x, fork_y), (ping_x, gh_top)]))
    # Below the fork horizontal (the stem has already ended) so the pill
    # does not sit on the T-junction.
    parts.append(pill(bot_cx, fork_y + 24, "diagnose"))

    # Clear gap under the VPC stroke; type sits *inside* the dashed footer
    # with padding so the bold line is not on the top border.
    gate_y = col_bottom + 14
    gate_h = 58
    parts.append(
        f'  <rect x="16" y="{gate_y:.0f}" width="1888" height="{gate_h:.0f}" rx="16" fill="#FFFFFF" '
        f'stroke="#D1D5DB" stroke-dasharray="7 6"/>'
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 28:.0f}" text-anchor="middle" class="gate">'
        "The bot has no control path into the lab: it only receives webhooks and writes GitHub issues.</text>"
    )
    parts.append(
        f'  <text x="960" y="{gate_y + 48:.0f}" text-anchor="middle" class="gate-sub">'
        "AWS/EC2 is optional: docker compose up runs the same lab (agents need --profile agents). "
        "The bridge needs outbound HTTPS to the bot; agents also call Anthropic.</text>"
    )

    card_y = gate_y + gate_h + 6

    def card2(n: int, x: float, line1: str, line2: str) -> str:
        return f"""  <g transform="translate({x:.0f},{card_y:.0f})">
    <rect width="592" height="56" rx="14" fill="#FFF7ED" stroke="#FDBA74"/>
    <text x="24" y="26" class="card-n">{n}.</text>
    <text x="52" y="26" class="card-t">{line1}</text>
    <text x="52" y="48" class="card-t">{line2}</text>
  </g>"""

    parts.append(card2(
        1, 16,
        "Held fault (FAULT_HOLD_SECONDS, default 120)",
        "or a real outage trips a Prometheus alert rule.",
    ))
    parts.append(card2(2, 664, "Bridge adds PromQL + jsonl and posts", "enriched JSON to the bot."))
    parts.append(card2(3, 1312, "Bot diagnoses and files or", "updates a GitHub issue."))

    parts.append("</svg>\n")
    return "\n".join(parts)


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
