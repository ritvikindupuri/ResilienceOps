#!/usr/bin/env python3
"""Build docs/architecture.svg in the Grok-bot-repo icon style.

Official marks live in docs/icons/:
- AWS Architecture Icons asset package (service + resource + group logos):
  https://aws.amazon.com/architecture/icons/
  Icon-package_07312026 (Simple Storage Service, Systems Manager,
  Systems Manager Parameter Store resource icon, Amazon EC2, AWS Cloud logo).
- Terraform / Docker / Prometheus / Grafana / GitHub: official brand glyphs
  via Simple Icons (CC0), project brand hex.
- k3s: official mark from CNCF artwork (projects/k3s).
- Alertmanager: Grafana data-source mark.

Generic person / clock / bell / document / traffic symbols are drawn here.
The Grok bot avatar is the real mark: a rounded hexagon tilted ~22°,
fill #FB2B3E, with two upright white capsule eyes.
"""

from __future__ import annotations

import base64
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "docs" / "icons"
OUT = ROOT / "docs" / "architecture.svg"

GROK_RED = "#FB2B3E"  # rgb(251, 43, 62) — actual bot fill
INC_ORANGE = "#EA580C"
REM_BLUE = "#2563EB"
REM_CAPSULE = "#F59E0B"

# Native sizes. README shows the figure at 950 px wide; keep ≥13 px effective.
# A tighter canvas + larger type so the PNG is readable at README width.
ICON = 56
NAME_PX = 28
CAP_PX = 24
GROUP_PX = 22
TITLE_PX = 36
GROUP_ICON = 48
DISPLAY_W = 950.0
MIN_EFFECTIVE_PX = 13.0

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
    "aws-param-store",
    "aws-logo",
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


def node(
    x: float,
    y: float,
    icon: str,
    name: str,
    cap: str,
    size: float = ICON,
    cap2: str = "",
    name2: str = "",
) -> str:
    top = -size - 10
    name_svg = f'    <text class="name" y="24" text-anchor="middle">{name}</text>\n'
    cap_y, cap2_y = 52, 76
    if name2:
        name_svg = (
            f'    <text class="name" y="16" text-anchor="middle">{name}</text>\n'
            f'    <text class="name" y="50" text-anchor="middle">{name2}</text>\n'
        )
        cap_y, cap2_y = 74, 98
    cap_svg = (
        f'    <text class="cap" y="{cap_y}" text-anchor="middle">{cap}</text>\n' if cap else ""
    )
    if cap2:
        cap_svg += f'    <text class="cap" y="{cap2_y}" text-anchor="middle">{cap2}</text>\n'
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{top:.1f}" width="{size:.0f}" height="{size:.0f}"/>
{name_svg}{cap_svg}  </g>"""


def _rounded_hexagon_path(radius: float = 42, corner: float = 7) -> str:
    verts = []
    for i in range(6):
        ang = math.radians(i * 60)
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


def remediator_avatar(x: float, y: float) -> str:
    """Orange capsule with two white eyes — drawn, no pale tile, hex-sized."""
    w, h = 96.0, 56.0
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <title>Incident Remediation</title>
    <rect x="{-w / 2:.1f}" y="{-h - 8:.1f}" width="{w:.0f}" height="{h:.0f}" rx="{h / 2:.1f}" fill="{REM_CAPSULE}"/>
    <rect x="-18" y="{-h / 2 - 18:.1f}" width="8" height="18" rx="4" fill="#FFFFFF"/>
    <rect x="10" y="{-h / 2 - 18:.1f}" width="8" height="18" rx="4" fill="#FFFFFF"/>
    <text class="name" y="36" text-anchor="middle">Incident</text>
    <text class="name" y="64" text-anchor="middle">Remediation</text>
    <text class="cap" y="88" text-anchor="middle">proposes a fix</text>
  </g>"""


def grok_avatar(x: float, y: float, name: str, cap: str) -> str:
    path = _rounded_hexagon_path()
    cap_svg = (
        f'    <text class="cap" y="70" text-anchor="middle">{cap}</text>\n' if cap else ""
    )
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <title>AI Incident Diagnosis</title>
    <g transform="translate(0,-32) rotate(23)">
      <path d="{path}" fill="{GROK_RED}"/>
    </g>
    <g transform="translate(-12,-43)">
      <rect x="-8" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
      <rect x="1.2" y="-6.6" width="6" height="13.2" rx="3" fill="#FFFFFF"/>
    </g>
    <text class="name" y="36" text-anchor="middle">AI Incident</text>
    <text class="name" y="64" text-anchor="middle">Diagnosis</text>
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
    palettes = {
        None: {
            "fill": "#F8FAFC",
            "stroke": "#E5E7EB",
            "sw": "1.5",
            "dash": "",
            "rx": "18",
            "cls": "group",
        },
        "account": {
            "fill": "#F8FAFC",
            "stroke": "#94A3B8",
            "sw": "1.6",
            "dash": "",
            "rx": "10",
            "cls": "group",
        },
        "host": {
            "fill": "#FFFFFF",
            "stroke": "#8C4FFF",
            "sw": "2.2",
            "dash": ' stroke-dasharray="7 5"',
            "rx": "8",
            "cls": "group-vpc",
        },
        "optional": {
            "fill": "#FAFBFC",
            "stroke": "#94A3B8",
            "sw": "1.6",
            "dash": ' stroke-dasharray="5 4"',
            "rx": "8",
            "cls": "group",
        },
        "bot": {
            "fill": "#FFF7F7",
            "stroke": "#FECACA",
            "sw": "1.6",
            "dash": "",
            "rx": "18",
            "cls": "group",
        },
    }
    pal = palettes[style]
    icon_svg = ""
    text_x = x + 18
    if icon:
        icon_svg = (
            f'  <use href="#i-{icon}" xlink:href="#i-{icon}" '
            f'x="{x + 12:.0f}" y="{y + 10:.0f}" width="{GROUP_ICON}" height="{GROUP_ICON}"/>\n'
        )
        text_x = x + 18 + GROUP_ICON
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="{pal["rx"]}" fill="{pal["fill"]}" stroke="{pal["stroke"]}" '
        f'stroke-width="{pal["sw"]}"{pal["dash"]}/>\n'
        f"{icon_svg}"
        f'  <text x="{text_x:.0f}" y="{y + 38:.0f}" class="{pal["cls"]}">{label}</text>'
    )


def _stroke(
    inc: bool, dashed: bool, thin: bool = False, rem: bool = False
) -> tuple[str, str, str]:
    if rem and thin:
        cls = "arrow-rem-thin"
    elif rem:
        cls = "arrow-rem"
    elif inc and thin:
        cls = "arrow-inc-thin"
    elif inc:
        cls = "arrow-inc"
    elif thin:
        cls = "arrow-thin"
    else:
        cls = "arrow"
    if rem:
        mk = "arr-rem"
    elif inc:
        mk = "arr-inc"
    else:
        mk = "arr"
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    return cls, mk, dash


def arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    dashed: bool = False,
    inc: bool = False,
    thin: bool = False,
    rem: bool = False,
) -> str:
    cls, mk, dash = _stroke(inc, dashed, thin=thin, rem=rem)
    return (
        f'  <line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
        f'class="{cls}"{dash} marker-end="url(#{mk})"/>'
    )


def poly(
    points: list[tuple[float, float]],
    dashed: bool = False,
    marked: bool = True,
    inc: bool = False,
    thin: bool = False,
    rem: bool = False,
) -> str:
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in points)
    cls, mk, dash = _stroke(inc, dashed, thin=thin, rem=rem)
    end = f' marker-end="url(#{mk})"' if marked else ""
    return (
        f'  <polyline points="{pts}" fill="none" class="{cls}" '
        f'stroke-linejoin="round" stroke-linecap="round"{dash}{end}/>'
    )


def satellite(
    x: float,
    y: float,
    icon: str,
    name: str,
    cap: str,
    size: float = 30,
    label_side: str = "below",
    name_size: int = 22,
) -> str:
    if label_side == "below":
        return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" y="{size / 2 + 22:.0f}" text-anchor="middle"
          style="font:700 {name_size}px Arial, Helvetica, sans-serif">{name}</text>
    <text class="cap" y="{size / 2 + 46:.0f}" text-anchor="middle">{cap}</text>
  </g>"""
    tx, anchor = (size / 2 + 12, "start") if label_side == "right" else (-(size / 2 + 12), "end")
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
    <use href="#i-{icon}" xlink:href="#i-{icon}" x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.0f}" height="{size:.0f}"/>
    <text class="name" x="{tx:.0f}" y="0" text-anchor="{anchor}"
          style="font:700 {name_size}px Arial, Helvetica, sans-serif">{name}</text>
    <text class="cap" x="{tx:.0f}" y="24" text-anchor="{anchor}">{cap}</text>
  </g>"""


def _tw(text: str, size: float, bold: bool = False) -> float:
    return size * (0.62 if bold else 0.55) * max(len(text), 1)


def _ic(node_y: float, size: float = ICON) -> float:
    return node_y - size / 2 - 10


def _icon_top(node_y: float, size: float = ICON) -> float:
    return node_y - size - 10


EPS = 1.6
CLIP_HIT = 7.0
NEAR_GAP = 16.0
CANVAS_MARGIN = 32.0
CONTAINER_PAD = 3.0
TEXT_CLEARANCE = 10.0
TEXT_ASCENT = 0.92
OUTSIDE_PAD = 8.0


def _polyline_id(name: str) -> str:
    if ":" in name:
        head, tail = name.rsplit(":", 1)
        if tail.isdigit():
            return head
    return name


def _share_endpoint(s1: tuple, s2: tuple) -> bool:
    for ax, ay in ((s1[0], s1[1]), (s1[2], s1[3])):
        for bx, by in ((s2[0], s2[1]), (s2[2], s2[3])):
            if abs(ax - bx) <= EPS and abs(ay - by) <= EPS:
                return True
    return False


def _pt_in_box(px: float, py: float, box: tuple, slop: float) -> bool:
    return (
        box[0] - slop <= px <= box[0] + box[2] + slop
        and box[1] - slop <= py <= box[1] + box[3] + slop
    )


def _endpoint_in_box(s: tuple, box: tuple, slop: float = 8.0) -> bool:
    return _pt_in_box(s[0], s[1], box, slop) or _pt_in_box(s[2], s[3], box, slop)


def _owned_labels(src: str, dst: str) -> frozenset[str]:
    """Text/icon names an edge may touch: only its own source and target."""
    labels: set[str] = set()
    for node in (src, dst):
        if not node:
            continue
        labels.add(node)
        rest = node.split(":", 1)[-1]
        labels.add(rest)
        for prefix in (
            "name:",
            "name2:",
            "cap:",
            "cap2:",
            "cap3:",
            "icon:",
            "sat:",
            "sat-cap:",
            "sat-icon:",
        ):
            labels.add(f"{prefix}{rest}")
    return frozenset(labels)


def _text_belongs(text_name: str, touch: frozenset[str]) -> bool:
    """Exact match only — no name:/cap: prefix whitelist for bystanders."""
    return bool(touch) and text_name in touch


def _ranges_overlap(a1: float, a2: float, b1: float, b2: float) -> tuple[float, float] | None:
    lo, hi = max(min(a1, a2), min(b1, b2)), min(max(a1, a2), max(b1, b2))
    if hi - lo > EPS:
        return lo, hi
    return None


def _hv_cross(h: tuple, v: tuple) -> bool:
    hy = h[1]
    vx = v[0]
    hx1, hx2 = min(h[0], h[2]), max(h[0], h[2])
    vy1, vy2 = min(v[1], v[3]), max(v[1], v[3])
    interior_h = hx1 + EPS < vx < hx2 - EPS
    interior_v = vy1 + EPS < hy < vy2 - EPS
    return interior_h and interior_v


def _collinear_overlap(s1: tuple, s2: tuple, horizontal: bool) -> bool:
    if horizontal:
        if abs(s1[1] - s2[1]) > 1.0:
            return False
        return _ranges_overlap(s1[0], s1[2], s2[0], s2[2]) is not None
    if abs(s1[0] - s2[0]) > 1.0:
        return False
    return _ranges_overlap(s1[1], s1[3], s2[1], s2[3]) is not None


def _proper_intersect(s1: tuple, s2: tuple) -> bool:
    h1 = abs(s1[1] - s1[3]) < 0.6
    v1 = abs(s1[0] - s1[2]) < 0.6
    h2 = abs(s2[1] - s2[3]) < 0.6
    v2 = abs(s2[0] - s2[2]) < 0.6
    if h1 and v2:
        return _hv_cross(s1, s2)
    if v1 and h2:
        return _hv_cross(s2, s1)
    if h1 and h2:
        return _collinear_overlap(s1, s2, True)
    if v1 and v2:
        return _collinear_overlap(s1, s2, False)
    return False


def _near_miss_orthogonal(s1: tuple, s2: tuple) -> bool:
    h = v = None
    if abs(s1[1] - s1[3]) < 0.6 and abs(s2[0] - s2[2]) < 0.6:
        h, v = s1, s2
    elif abs(s2[1] - s2[3]) < 0.6 and abs(s1[0] - s1[2]) < 0.6:
        h, v = s2, s1
    else:
        return False
    hy, vx = h[1], v[0]
    hx1, hx2 = min(h[0], h[2]), max(h[0], h[2])
    vy1, vy2 = min(v[1], v[3]), max(v[1], v[3])
    if not (hx1 + EPS < vx < hx2 - EPS):
        return False
    if vy1 + EPS < hy < vy2 - EPS:
        return True
    dist = min(abs(hy - vy1), abs(hy - vy2))
    vlen = abs(v[1] - v[3])
    return dist > EPS and dist < NEAR_GAP and vlen >= 80.0


def _seg_clip_len(s: tuple, box: tuple) -> float:
    x, y, w, h = box[0], box[1], box[2], box[3]
    l, t, r, b = x, y, x + w, y + h
    x1, y1, x2, y2 = s[0], s[1], s[2], s[3]
    if abs(y1 - y2) < 0.6:
        if y1 < t + EPS or y1 > b - EPS:
            return 0.0
        ov = _ranges_overlap(x1, x2, l, r)
        return 0.0 if ov is None else ov[1] - ov[0]
    if abs(x1 - x2) < 0.6:
        if x1 < l + EPS or x1 > r - EPS:
            return 0.0
        ov = _ranges_overlap(y1, y2, t, b)
        return 0.0 if ov is None else ov[1] - ov[0]
    return 0.0


class Scene:
    """Orthogonal arrows + bboxes, with a no-crossing checker."""

    def __init__(self, width: float, height: float, margin: float = CANVAS_MARGIN) -> None:
        self.parts: list[str] = []
        self.segments: list[tuple[float, float, float, float, str]] = []
        self.boxes: list[tuple[float, float, float, float, str, str]] = []
        self.containers: dict[str, tuple[float, float, float, float]] = {}
        self.membership: dict[str, str] = {}
        self.fonts: list[tuple[str, float]] = []
        self.heads: dict[str, int] = {}
        self.width = width
        self.height = height
        self.margin = margin

    def add(self, svg: str) -> None:
        self.parts.append(svg)

    def container(self, name: str, x: float, y: float, w: float, h: float) -> None:
        self.containers[name] = (x, y, w, h)
        self.boxes.append((x, y, w, h, f"group:{name}", "group"))

    def box(self, x: float, y: float, w: float, h: float, name: str, kind: str, container: str = "") -> None:
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        self.boxes.append((x, y, w, h, name, kind))
        if container:
            self.membership[name] = container

    def text(
        self,
        x: float,
        baseline: float,
        value: str,
        size: float,
        *,
        bold: bool = False,
        anchor: str = "start",
        name: str = "",
        container: str = "",
    ) -> None:
        width = _tw(value, size, bold)
        if anchor == "middle":
            left = x - width / 2
        elif anchor == "end":
            left = x - width
        else:
            left = x
        label = name or value
        # Ascent ≈ 0.92 em so a clipped title (cap-height only) fails the canvas-margin check.
        self.box(
            left,
            baseline - TEXT_ASCENT * size,
            width,
            size * (TEXT_ASCENT + 0.22),
            label,
            "text",
            container=container,
        )
        self.fonts.append((label, size))

    def icon(self, cx: float, top: float, size: float, name: str, container: str = "") -> None:
        self.box(cx - size / 2, top, size, size, name, "icon", container=container)

    def add_seg(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        name: str,
        touch: frozenset[str] = frozenset(),
        inc: bool = False,
        rem: bool = False,
    ) -> None:
        if abs(x1 - x2) < 0.5 and abs(y1 - y2) < 0.5:
            return
        self.segments.append((x1, y1, x2, y2, name, touch, inc, rem))

    def _mark(self, name: str, marked: bool) -> None:
        if marked:
            self.heads[name] = self.heads.get(name, 0) + 1

    def poly(
        self,
        points: list[tuple[float, float]],
        *,
        dashed: bool = False,
        marked: bool = True,
        inc: bool = False,
        thin: bool = False,
        rem: bool = False,
        name: str = "edge",
        src: str = "",
        dst: str = "",
        touch: tuple[str, ...] = (),
    ) -> None:
        self.add(poly(points, dashed=dashed, marked=marked, inc=inc, thin=thin, rem=rem))
        self._mark(name, marked)
        owned = _owned_labels(src, dst) | frozenset(touch)
        for i in range(len(points) - 1):
            self.add_seg(*points[i], *points[i + 1], f"{name}:{i}", owned, inc=inc, rem=rem)

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        dashed: bool = False,
        inc: bool = False,
        thin: bool = False,
        rem: bool = False,
        name: str = "edge",
        src: str = "",
        dst: str = "",
        touch: tuple[str, ...] = (),
    ) -> None:
        self.add(arrow(x1, y1, x2, y2, dashed=dashed, inc=inc, thin=thin, rem=rem))
        self._mark(name, True)
        owned = _owned_labels(src, dst) | frozenset(touch)
        self.add_seg(x1, y1, x2, y2, name, owned, inc=inc, rem=rem)

    def node_at(
        self,
        x: float,
        y: float,
        icon: str,
        name: str,
        cap: str,
        size: float = ICON,
        cap2: str = "",
        name2: str = "",
        container: str = "",
        name_size: float = NAME_PX,
        cap_size: float = CAP_PX,
    ) -> None:
        self.add(node(x, y, icon, name, cap, size=size, cap2=cap2, name2=name2))
        self.icon(x, _icon_top(y, size), size, f"icon:{name}", container=container)
        if name2:
            self.text(x, y + 16, name, name_size, bold=True, anchor="middle", name=f"name:{name}", container=container)
            self.text(x, y + 50, name2, name_size, bold=True, anchor="middle", name=f"name2:{name}", container=container)
            cap_y, cap2_y = y + 74, y + 98
        else:
            self.text(x, y + 24, name, name_size, bold=True, anchor="middle", name=f"name:{name}", container=container)
            cap_y, cap2_y = y + 52, y + 76
        if cap:
            self.text(x, cap_y, cap, cap_size, anchor="middle", name=f"cap:{name}", container=container)
        if cap2:
            self.text(x, cap2_y, cap2, cap_size, anchor="middle", name=f"cap2:{name}", container=container)

    def satellite_at(
        self,
        x: float,
        y: float,
        icon: str,
        name: str,
        cap: str,
        size: float = 30,
        label_side: str = "below",
        name_size: int = 22,
        container: str = "",
    ) -> None:
        self.add(satellite(x, y, icon, name, cap, size=size, label_side=label_side, name_size=name_size))
        self.icon(x, y - size / 2, size, f"sat-icon:{name}", container=container)
        if label_side == "below":
            self.text(
                x, y + size / 2 + 22, name, name_size, bold=True, anchor="middle",
                name=f"sat:{name}", container=container,
            )
            if cap:
                self.text(
                    x, y + size / 2 + 46, cap, CAP_PX, anchor="middle",
                    name=f"sat-cap:{name}", container=container,
                )
        else:
            tx = x + size / 2 + 12
            self.text(tx, y, name, name_size, bold=True, anchor="start", name=f"sat:{name}", container=container)
            if cap:
                self.text(tx, y + 24, cap, CAP_PX, anchor="start", name=f"sat-cap:{name}", container=container)

    def grok_at(self, x: float, y: float, name: str, container: str = "") -> None:
        self.add(grok_avatar(x, y, name, ""))
        self.box(x - 48, y - 80, 96, 96, "icon:grok", "icon", container=container)
        self.text(x, y + 36, "AI Incident", NAME_PX, bold=True, anchor="middle", name="name:grok1", container=container)
        self.text(x, y + 64, "Diagnosis", NAME_PX, bold=True, anchor="middle", name="name:grok2", container=container)

    def remediator_at(self, x: float, y: float, container: str = "") -> None:
        self.add(remediator_avatar(x, y))
        self.box(x - 48, y - 64, 96, 56, "icon:remediator", "icon", container=container)
        self.text(x, y + 36, "Incident", NAME_PX, bold=True, anchor="middle", name="name:remediator1", container=container)
        self.text(x, y + 64, "Remediation", NAME_PX, bold=True, anchor="middle", name="name:remediator2", container=container)
        self.text(x, y + 88, "proposes a fix", CAP_PX, anchor="middle", name="cap:remediator", container=container)

    def badge(self, x: float, y: float, n: int, container: str = "", rem: bool = False) -> None:
        r = 15
        fill = REM_BLUE if rem else INC_ORANGE
        self.add(
            f'  <g transform="translate({x:.0f},{y:.0f})">'
            f'<circle r="{r}" fill="{fill}" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text text-anchor="middle" dy="7" class="badge">{n}</text></g>'
        )
        self.box(x - r, y - r, 2 * r, 2 * r, f"badge:{n}", "badge", container=container)
        self.fonts.append((f"badge:{n}", 22))

    def check(self) -> list[str]:
        hits: list[str] = []
        # Shared collinear of *different* edges always fails, even at a T.
        # T-junctions (shared endpoint, no interior overlap) are allowed.
        # Any orange × grey interior cross fails.
        for i, s1 in enumerate(self.segments):
            e1 = _polyline_id(s1[4])
            inc1 = s1[6] if len(s1) > 6 else False
            rem1 = s1[7] if len(s1) > 7 else False
            k1 = "rem" if rem1 else ("diag" if inc1 else "grey")
            h1 = abs(s1[1] - s1[3]) < 0.6
            v1 = abs(s1[0] - s1[2]) < 0.6
            for s2 in self.segments[i + 1 :]:
                e2 = _polyline_id(s2[4])
                inc2 = s2[6] if len(s2) > 6 else False
                rem2 = s2[7] if len(s2) > 7 else False
                k2 = "rem" if rem2 else ("diag" if inc2 else "grey")
                h2 = abs(s2[1] - s2[3]) < 0.6
                v2 = abs(s2[0] - s2[2]) < 0.6
                collinear = False
                if h1 and h2:
                    collinear = _collinear_overlap(s1, s2, True)
                elif v1 and v2:
                    collinear = _collinear_overlap(s1, s2, False)
                if collinear and e1 != e2:
                    hits.append(
                        f"shared collinear {e1} × {e2} "
                        f"({s1[4]} {s1[0]:.0f},{s1[1]:.0f}-{s1[2]:.0f},{s1[3]:.0f} / "
                        f"{s2[4]} {s2[0]:.0f},{s2[1]:.0f}-{s2[2]:.0f},{s2[3]:.0f})"
                    )
                    continue
                if _share_endpoint(s1, s2):
                    continue
                if _proper_intersect(s1, s2):
                    kind = f"{k1} × {k2}" if k1 != k2 else "polylines"
                    hits.append(
                        f"{kind} {e1} × {e2} "
                        f"({s1[4]} {s1[0]:.0f},{s1[1]:.0f}-{s1[2]:.0f},{s1[3]:.0f} / "
                        f"{s2[4]} {s2[0]:.0f},{s2[1]:.0f}-{s2[2]:.0f},{s2[3]:.0f})"
                    )
        # Text: 10px halo unless the label is this edge's own source/target.
        for s in self.segments:
            touch = s[5] if len(s) > 5 else frozenset()
            for b in self.boxes:
                if b[5] != "text":
                    continue
                if _text_belongs(b[4], touch):
                    continue
                inf = (
                    b[0] - TEXT_CLEARANCE,
                    b[1] - TEXT_CLEARANCE,
                    b[2] + 2 * TEXT_CLEARANCE,
                    b[3] + 2 * TEXT_CLEARANCE,
                )
                if _seg_clip_len(s, inf) > 0.5:
                    hits.append(f"line {s[4]} through text {b[4]}")
        # Boxes: a segment may only clip a box it starts or ends in.
        # Background frames (host/compose/deploy/external/k3s) are not obstacles;
        # node-like groups (Agents, Target services) may only be touched at the border.
        background = {
            "group:deploy",
            "group:laptop",
            "group:aws",
            "group:host",
            "group:compose",
            "group:bot",
            "group:k3s",
        }
        solid_groups = {"group:agents", "group:services"}
        for s in self.segments:
            for b in self.boxes:
                if b[5] in {"icon", "badge"}:
                    if _endpoint_in_box(s, b):
                        continue
                    if _seg_clip_len(s, b) > CLIP_HIT:
                        hits.append(f"line {s[4]} through {b[5]} {b[4]}")
                elif b[5] == "group":
                    if b[4] in background:
                        continue
                    clip = _seg_clip_len(s, b)
                    in1 = _pt_in_box(s[0], s[1], b, 8.0)
                    in2 = _pt_in_box(s[2], s[3], b, 8.0)
                    if b[4] in solid_groups:
                        # Start or end inside (e.g. ① from the Red icon) and exit
                        # the right edge. A flyover that only clips the fill still fails.
                        if in1 or in2:
                            continue
                        if clip > 16.0:
                            hits.append(f"line {s[4]} through {b[5]} {b[4]}")
                    else:
                        if in1 or in2:
                            continue
                        if clip > 2.0:
                            hits.append(f"line {s[4]} through {b[5]} {b[4]}")
        skip = ("group:", "title", "k3s-sub", "foot", "legend", "host-title", "host-sg")
        for i, b1 in enumerate(self.boxes):
            if b1[5] not in {"text", "icon", "badge"}:
                continue
            if any(b1[4].startswith(p) for p in skip):
                continue
            for b2 in self.boxes[i + 1 :]:
                if b2[5] not in {"text", "icon", "badge"}:
                    continue
                if any(b2[4].startswith(p) for p in skip):
                    continue
                ox = _ranges_overlap(b1[0], b1[0] + b1[2], b2[0], b2[0] + b2[2])
                oy = _ranges_overlap(b1[1], b1[1] + b1[3], b2[1], b2[1] + b2[3])
                if ox and oy and (ox[1] - ox[0]) > 8 and (oy[1] - oy[0]) > 6:
                    hits.append(f"bbox {b1[5]} {b1[4]} × {b2[5]} {b2[4]}")
        m = self.margin
        for b in self.boxes:
            if b[5] not in {"text", "icon", "badge"}:
                continue
            l, t, r, bot = b[0], b[1], b[0] + b[2], b[1] + b[3]
            if l < m - 0.5 or t < m - 0.5 or r > self.width - m + 0.5 or bot > self.height - m + 0.5:
                hits.append(f"canvas {b[5]} {b[4]} ({l:.0f},{t:.0f})-({r:.0f},{bot:.0f})")
            cname = self.membership.get(b[4])
            if cname and cname in self.containers:
                cx, cy, cw, ch = self.containers[cname]
                if (
                    l < cx + CONTAINER_PAD
                    or t < cy + CONTAINER_PAD
                    or r > cx + cw - CONTAINER_PAD
                    or bot > cy + ch - CONTAINER_PAD
                ):
                    hits.append(f"container {cname} {b[5]} {b[4]}")
            elif b[5] == "text":
                for gname, (cx, cy, cw, ch) in self.containers.items():
                    ox = _ranges_overlap(l, r, cx, cx + cw)
                    oy = _ranges_overlap(t, bot, cy, cy + ch)
                    if ox and oy and (ox[1] - ox[0]) > OUTSIDE_PAD and (oy[1] - oy[0]) > OUTSIDE_PAD:
                        hits.append(f"outside {b[4]} overlaps container {gname}")
        scale = DISPLAY_W / self.width
        for label, size in self.fonts:
            eff = size * scale
            if eff + 1e-6 < MIN_EFFECTIVE_PX:
                hits.append(f"font {label} native {size:.0f}px → {eff:.1f}px at {DISPLAY_W:.0f}px")
        for name, count in self.heads.items():
            if count != 1:
                hits.append(f"arrowheads {name}={count}")
        return hits


def build() -> str:
    svg, _violations = build_scene()
    return svg


def build_scene() -> tuple[str, list[str]]:
    # Cropped canvas: content fills the frame so 24px captions read ~15px at README width.
    W, H = 1480, 1340
    scene = Scene(W, H)

    dep_x0, dep_y, dep_w, dep_h = 32, 70, 1416, 204
    tf_x, ec2_x, dep_node_y = 500, 880, 198
    drop_x = 880

    host_x, host_y, host_w, host_h = 32, 278, 1056, 890
    bot_x, bot_y, bot_w, bot_h = 1112, 278, 336, 948

    compose_x, compose_y, compose_w, compose_h = 48, 362, 1024, 536
    k3s_x, k3s_y, k3s_w, k3s_h = 48, 1050, 490, 72

    agents_x, agents_y, agents_w, agents_h = 62, 426, 250, 456
    red_x, red_y = 187, 546
    blue_x, blue_y = 187, 806

    svc_x, svc_y, svc_w, svc_h = 336, 426, 214, 456
    svc_cx = 443
    gw_y, os_y, ps_y = 546, 676, 806

    prom_x, am_x, br_x = 640, 800, 950
    prom_y = am_y = br_y = 546
    graf_x, graf_y = 800, 806

    # External column: Diagnosis → GitHub → Remediation → Owner / Actions.
    # Owner ping sits centered above Diagnosis (not on the External edge).
    grok_x, grok_y = 1280, 546
    ping_x, ping_y = 1280, 365
    gh_x, gh_y = 1280, 700
    rem_x, rem_y = 1280, 880
    own_x, own_y = 1280, 1160
    act_x, act_y = 1176, 1040
    poll_x, poll_y = 820, 1035
    corridor_x = 578
    col_left = 1140

    scene.add(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"
     aria-label="How ResilienceOps plus the diagnosis and remediator bots work">
  <desc>How ResilienceOps plus the diagnosis and remediator bots work</desc>
  <defs>
    <style>
      .title {{ font: 700 {TITLE_PX}px Arial, Helvetica, sans-serif; fill: #111827; }}
      .group {{ font: 600 {GROUP_PX}px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .group-vpc {{ font: 600 {GROUP_PX}px Arial, Helvetica, sans-serif; fill: #5B3BB4; }}
      .name {{ font: 700 {NAME_PX}px Arial, Helvetica, sans-serif; fill: #111827; }}
      .cap {{ font: {CAP_PX}px Arial, Helvetica, sans-serif; fill: #6B7280; }}
      .foot {{ font: {CAP_PX}px Arial, Helvetica, sans-serif; fill: #374151; }}
      .legend {{ font: {CAP_PX}px Arial, Helvetica, sans-serif; fill: #4B5563; }}
      .badge {{ font: 700 22px Arial, Helvetica, sans-serif; fill: #FFFFFF; }}
      .arrow {{ stroke: #9CA3AF; stroke-width: 2.0; fill: none; }}
      .arrow-thin {{ stroke: #9CA3AF; stroke-width: 1.35; fill: none; }}
      .arrow-inc {{ stroke: {INC_ORANGE}; stroke-width: 3.4; fill: none; }}
      .arrow-inc-thin {{ stroke: {INC_ORANGE}; stroke-width: 2.0; fill: none; }}
      .arrow-rem {{ stroke: {REM_BLUE}; stroke-width: 3.4; fill: none; }}
      .arrow-rem-thin {{ stroke: {REM_BLUE}; stroke-width: 2.0; fill: none; }}
    </style>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#9CA3AF"/>
    </marker>
    <marker id="arr-inc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{INC_ORANGE}"/>
    </marker>
    <marker id="arr-rem" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{REM_BLUE}"/>
    </marker>
{symbols()}
  </defs>
  <rect width="{W}" height="{H}" fill="#FFFFFF"/>
    <text x="{W / 2:.0f}" y="68" text-anchor="middle" class="title">How ResilienceOps plus the diagnosis and remediator bots work</text>
""")
    scene.text(
        W / 2, 68, "How ResilienceOps plus the diagnosis and remediator bots work",
        TITLE_PX, bold=True, anchor="middle", name="title",
    )

    scene.add(group(dep_x0, dep_y, dep_w, dep_h, "Deploy (optional AWS)", icon="aws-logo", style="account"))
    scene.container("deploy", dep_x0, dep_y, dep_w, dep_h)
    scene.text(
        dep_x0 + 18 + GROUP_ICON, dep_y + 38, "Deploy (optional AWS)",
        GROUP_PX, bold=True, name="group:deploy", container="deploy",
    )

    scene.node_at(tf_x, dep_node_y, "terraform", "Terraform", "creates the infra", container="deploy")
    scene.node_at(ec2_x, dep_node_y, "aws-ec2", "EC2", "lab host", container="deploy")

    host_title = "EC2 host · public subnet 10.0.1.0/24 · VPC 10.0.0.0/16"
    host_sg = "Grafana and API ports from your IP"
    scene.add(group(host_x, host_y, host_w, host_h, host_title, icon="aws-ec2", style="host"))
    scene.container("host", host_x, host_y, host_w, host_h)
    scene.text(
        host_x + 18 + GROUP_ICON, host_y + 38, host_title,
        GROUP_PX, bold=True, name="host-title", container="host",
    )
    scene.add(f'  <text x="{host_x + 18 + GROUP_ICON:.0f}" y="{host_y + 62:.0f}" class="cap">{host_sg}</text>')
    scene.text(host_x + 18 + GROUP_ICON, host_y + 62, host_sg, CAP_PX, name="host-sg", container="host")
    scene.add(group(bot_x, bot_y, bot_w, bot_h, "External", style="bot"))
    scene.container("bot", bot_x, bot_y, bot_w, bot_h)
    scene.text(bot_x + 18, bot_y + 38, "External", GROUP_PX, bold=True, name="group:bot", container="bot")

    scene.add(group(compose_x, compose_y, compose_w, compose_h, "Lab (Docker Compose)", icon="docker"))
    scene.container("compose", compose_x, compose_y, compose_w, compose_h)
    scene.text(
        compose_x + 18 + GROUP_ICON, compose_y + 38, "Lab (Docker Compose)",
        GROUP_PX, bold=True, name="group:compose", container="compose",
    )

    scene.add(group(agents_x, agents_y, agents_w, agents_h, "Agents", style=None))
    scene.container("agents", agents_x, agents_y, agents_w, agents_h)
    scene.text(agents_x + 18, agents_y + 38, "Agents", GROUP_PX, bold=True, name="group:agents", container="agents")

    scene.add(group(svc_x, svc_y, svc_w, svc_h, "Services", style=None))
    scene.container("services", svc_x, svc_y, svc_w, svc_h)
    scene.text(svc_x + 18, svc_y + 38, "Services", GROUP_PX, bold=True, name="group:services", container="services")

    k3s_title = "k3s sandbox (optional)"
    k3s_sub = "agents in one sandbox pod"
    scene.add(group(k3s_x, k3s_y, k3s_w, k3s_h, k3s_title, icon="k3s", style="optional"))
    scene.container("k3s", k3s_x, k3s_y, k3s_w, k3s_h)
    scene.text(
        k3s_x + 18 + GROUP_ICON, k3s_y + 38, k3s_title,
        GROUP_PX, bold=True, name="group:k3s", container="k3s",
    )
    scene.add(f'  <text x="{k3s_x + 18 + GROUP_ICON:.0f}" y="{k3s_y + 62:.0f}" class="cap">{k3s_sub}</text>')
    scene.text(k3s_x + 18 + GROUP_ICON, k3s_y + 62, k3s_sub, CAP_PX, name="k3s-sub", container="k3s")

    scene.node_at(
        red_x, red_y, "person-red", "Red Team", "faults order", cap2="+ payment", container="agents"
    )
    scene.node_at(
        blue_x, blue_y, "person-blue", "Blue Team", "watches and resets", container="agents"
    )
    scene.node_at(svc_cx, gw_y, "fastapi", "api-gw", "", container="services")
    scene.node_at(svc_cx, os_y, "fastapi", "order-", "", name2="service", container="services")
    scene.node_at(svc_cx, ps_y, "fastapi", "payment-", "", name2="service", container="services")
    scene.node_at(prom_x, prom_y, "prometheus", "Prometheus", "reads metrics", container="compose")
    scene.node_at(am_x, am_y, "alertmanager", "Alert", "", name2="manager", container="compose")
    scene.node_at(
        br_x, br_y, "document", "incident-", "queries Prometheus", name2="bridge", container="compose"
    )
    scene.node_at(graf_x, graf_y, "grafana", "Grafana", "dashboard", container="compose")
    scene.grok_at(grok_x, grok_y, "AI Incident Diagnosis", container="bot")
    scene.node_at(
        ping_x, ping_y, "bell", "Owner ping", "", size=40, name_size=22, cap_size=CAP_PX, container="bot"
    )
    scene.node_at(gh_x, gh_y, "github", "GitHub issue", "", container="bot")
    scene.remediator_at(rem_x, rem_y, container="bot")
    scene.node_at(own_x, own_y, "person", "Owner", "/approve", container="bot")
    scene.node_at(
        act_x, act_y, "github", "Actions", "records",
        name_size=22, cap_size=22, container="bot",
    )
    scene.node_at(
        poll_x, poll_y, "clock", "host poller", "or SSM", container="host"
    )

    row_a = _ic(gw_y)
    red_right = red_x + ICON / 2 + 4
    blue_right = blue_x + ICON / 2 + 4
    os_left = svc_cx - ICON / 2 - 4
    os_ic = _ic(os_y)
    ps_ic = _ic(ps_y)
    svc_left = svc_x
    svc_right = svc_x + svc_w
    prom_left = prom_x - ICON / 2 - 8
    prom_right = prom_x + ICON / 2 + 8
    am_left = am_x - ICON / 2 - 8
    am_right = am_x + ICON / 2 + 8
    br_left = br_x - ICON / 2 - 8
    br_right = br_x + ICON / 2 + 8
    grok_left = grok_x - 48
    grok_top = grok_y - 80
    ping_bot = ping_y - 10
    gh_top = _icon_top(gh_y)
    rem_top = rem_y - 64
    rem_bot = rem_y + 100
    own_top = _icon_top(own_y)
    own_left = own_x - ICON / 2 - 4
    own_ic = _ic(own_y)
    act_right = act_x + ICON / 2 + 4
    act_left = act_x - ICON / 2 - 4
    poll_right = poll_x + ICON / 2 + 8
    poll_left = poll_x - ICON / 2 - 8
    poll_ic = _ic(poll_y)
    fork_x = 320
    fork_ps_x = 308
    badge_y = row_a - 32
    query_y = 648
    blue_y_shaft = 780

    scene.arrow(
        tf_x + ICON / 2 + 8,
        _ic(dep_node_y),
        ec2_x - ICON / 2 - 8,
        _ic(dep_node_y),
        name="tf-ec2",
        src="icon:Terraform",
        dst="icon:EC2",
    )
    # Drop from under the EC2 caption into the host — long enough to read as an arrow.
    scene.arrow(
        drop_x,
        dep_node_y + 58,
        drop_x,
        host_y + 88,
        name="aws-host",
        src="icon:EC2",
    )

    # Red Team faults stay grey and unnumbered (not part of ①–⑥).
    scene.poly(
        [(red_right, row_a), (fork_x, row_a)],
        marked=False,
        name="fault-stem",
        src="icon:Red Team",
    )
    scene.poly(
        [(fork_x, row_a), (fork_x, os_ic), (os_left, os_ic)],
        name="fault-os",
        src="icon:Red Team",
        dst="icon:order-",
    )
    scene.poly(
        [(fork_ps_x, row_a), (fork_ps_x, ps_ic), (os_left, ps_ic)],
        name="fault-ps",
        src="icon:Red Team",
        dst="icon:payment-",
    )

    # Blue health-check / reset onto the services group (grey, above payment labels).
    scene.arrow(
        blue_right,
        blue_y_shaft,
        svc_left,
        blue_y_shaft,
        name="blue-svc",
        src="icon:Blue Team",
        dst="icon:payment-",
        touch=("name:Blue Team", "cap:Blue Team", "group:services"),
    )

    # ①–④ diagnosis row: scrape → alert → bridge → diagnosis bot.
    scene.arrow(
        svc_right, row_a, prom_left, row_a, inc=True, name="scrape",
        src="icon:api-gw", dst="icon:Prometheus",
    )
    scene.badge((svc_right + prom_left) / 2, badge_y, 1, container="compose")
    scene.arrow(
        prom_right, row_a, am_left, row_a, inc=True, name="prom-am",
        src="icon:Prometheus", dst="icon:Alert",
    )
    scene.badge((prom_x + am_x) / 2, badge_y, 2, container="compose")
    scene.arrow(
        am_right, row_a, br_left, row_a, inc=True, name="am-br",
        src="icon:Alert", dst="icon:incident-",
    )
    scene.badge((am_x + br_x) / 2, badge_y, 3, container="compose")
    scene.arrow(
        br_right, row_a, grok_left, row_a, inc=True, name="br-bot",
        src="icon:incident-", dst="icon:grok",
    )
    scene.badge(bot_x + 36, badge_y, 4, container="bot")

    # ⑤ Diagnosis → GitHub, around the labels (badge off the shaft).
    scene.poly(
        [
            (grok_left, grok_y - 16),
            (col_left, grok_y - 16),
            (col_left, gh_top - 8),
            (gh_x, gh_top - 8),
            (gh_x, gh_top),
        ],
        inc=True,
        name="bot-gh",
        src="icon:grok",
        dst="icon:GitHub issue",
    )
    scene.badge(1172, 590, 5, container="bot")

    # ⑥ Diagnosis → owner ping (centered above the hex, not on the box edge).
    scene.arrow(
        grok_x, grok_top, grok_x, ping_bot, inc=True, name="bot-ping",
        src="icon:grok", dst="icon:Owner ping",
    )
    scene.badge(grok_x - 36, (grok_top + ping_bot) / 2, 6, container="bot")

    # ⑦ GitHub → Remediation, ⑧ Remediation → Owner (blue, real length).
    scene.arrow(
        gh_x, gh_y + 48, rem_x, rem_top, rem=True, name="gh-rem",
        src="icon:GitHub issue",
        dst="icon:remediator",
        touch=("name:GitHub issue", "name:remediator1", "name:remediator2", "cap:remediator"),
    )
    scene.badge(gh_x + 40, (gh_y + 48 + rem_top) / 2, 7, rem=True, container="bot")
    scene.arrow(
        rem_x, rem_bot, own_x, own_top, rem=True, name="rem-own",
        src="icon:remediator",
        dst="icon:Owner",
        touch=("name:remediator1", "name:remediator2", "cap:remediator"),
    )
    scene.badge(rem_x + 40, (rem_bot + own_top) / 2, 8, rem=True, container="bot")

    # ⑨ Owner /approve → GitHub Actions records → host poller / SSM → services group.
    act_ic = _ic(act_y)
    highway_y = act_ic
    scene.poly(
        [(own_left, own_ic), (own_left, highway_y), (act_right, highway_y)],
        rem=True,
        name="own-act",
        src="icon:Owner",
        dst="icon:Actions",
    )
    scene.arrow(
        act_left, highway_y, poll_right, highway_y, rem=True, name="act-poll",
        src="icon:Actions",
        dst="icon:host poller",
    )
    scene.poly(
        [
            (poll_left, highway_y),
            (corridor_x, highway_y),
            (corridor_x, 750),
            (svc_right, 750),
        ],
        rem=True,
        name="poll-svc",
        src="icon:host poller",
        dst="icon:payment-",
        touch=("group:services", "name:host poller", "cap:host poller"),
    )
    scene.badge(corridor_x + 28, 860, 9, rem=True, container="host")

    # Supporting: Grafana read + dashed PromQL query (below the diagnosis row).
    scene.poly(
        [
            (prom_x, query_y + 28),
            (prom_x, _ic(graf_y)),
            (graf_x - ICON / 2 - 8, _ic(graf_y)),
        ],
        name="prom-graf",
        src="icon:Prometheus",
        dst="icon:Grafana",
    )
    scene.arrow(
        br_x, query_y, prom_x + ICON / 2 + 8, query_y, dashed=True, name="promql",
        src="icon:incident-", dst="icon:Prometheus",
        touch=("cap:incident-", "cap:Prometheus", "name2:incident-", "name:Prometheus"),
    )

    leg_y = 1276
    scene.add(
        f'  <line x1="36" y1="{leg_y}" x2="70" y2="{leg_y}" class="arrow-inc"/>'
        f'  <text x="80" y="{leg_y + 6}" class="legend">1–6 diagnosis path</text>'
        f'  <line x1="320" y1="{leg_y}" x2="354" y2="{leg_y}" class="arrow-rem"/>'
        f'  <text x="364" y="{leg_y + 6}" class="legend">7–9 remediator path</text>'
        f'  <line x1="620" y1="{leg_y}" x2="654" y2="{leg_y}" class="arrow"/>'
        f'  <text x="664" y="{leg_y + 6}" class="legend">supporting</text>'
    )
    scene.text(80, leg_y + 6, "1–6 diagnosis path", CAP_PX, name="legend-inc")
    scene.text(364, leg_y + 6, "7–9 remediator path", CAP_PX, name="legend-rem")
    scene.text(664, leg_y + 6, "supporting", CAP_PX, name="legend-sup")
    scene.add("</svg>\n")
    return "\n".join(scene.parts), scene.check()


def check_geometry() -> list[str]:
    _svg, violations = build_scene()
    return violations


def main() -> int:
    svg, violations = build_scene()
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT}")
    if violations:
        print(f"{len(violations)} geometry violation(s):")
        for item in violations[:80]:
            print(f"  {item}")
        if len(violations) > 80:
            print(f"  ... {len(violations) - 80} more")
        return 1
    print("geometry: 0 violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
