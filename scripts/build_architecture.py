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


def _tw(text: str, size: float, bold: bool = False) -> float:
    return size * (0.62 if bold else 0.55) * max(len(text), 1)


def _ic(node_y: float, size: float = ICON) -> float:
    """Vertical center of the icon drawn by node()."""
    return node_y - size / 2 - 8


def _icon_top(node_y: float, size: float = ICON) -> float:
    return node_y - size - 8


EPS = 1.6
CLIP_HIT = 7.0
NEAR_GAP = 28.0  # visual 1x: a vertical that stops just short of a horizontal at the same x
CANVAS_MARGIN = 28.0
CONTAINER_PAD = 3.0


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
    """Catch 1x 'looks like a cross': a vertical's x sits in a horizontal's
    interior, and the horizontal y is just outside the vertical's range.
    T-junctions (y on a vertical endpoint) are allowed."""
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
        return True  # true interior X (also reported by _hv_cross)
    dist = min(abs(hy - vy1), abs(hy - vy2))
    vlen = abs(v[1] - v[3])
    # Short ticks that stop before the next bus are stacked-lane gaps, not
    # crossings. Flag only a long riser that stops just shy of a flyover.
    return dist > EPS and dist < NEAR_GAP and vlen >= 80.0


def _seg_clip_len(s: tuple, box: tuple) -> float:
    x, y, w, h = box[0], box[1], box[2], box[3]
    l, t, r, b = x, y, x + w, y + h
    x1, y1, x2, y2 = s[0], s[1], s[2], s[3]
    if abs(y1 - y2) < 0.6:  # horizontal
        if y1 < t + EPS or y1 > b - EPS:
            return 0.0
        ov = _ranges_overlap(x1, x2, l, r)
        return 0.0 if ov is None else ov[1] - ov[0]
    if abs(x1 - x2) < 0.6:  # vertical
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
        self.width = width
        self.height = height
        self.margin = margin

    def add(self, svg: str) -> None:
        self.parts.append(svg)

    def container(self, name: str, x: float, y: float, w: float, h: float) -> None:
        self.containers[name] = (x, y, w, h)

    def box(self, x: float, y: float, w: float, h: float, name: str, kind: str, container: str = "") -> None:
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        self.boxes.append((x, y, w, h, name, kind))
        if container:
            self.membership[name] = container

    def text(self, x: float, baseline: float, value: str, size: float, *, bold: bool = False, anchor: str = "start", name: str = "", container: str = "") -> None:
        width = _tw(value, size, bold)
        if anchor == "middle":
            left = x - width / 2
        elif anchor == "end":
            left = x - width
        else:
            left = x
        self.box(left, baseline - 0.82 * size, width, size * 1.05, name or value, "text", container=container)

    def icon(self, cx: float, top: float, size: float, name: str) -> None:
        self.box(cx - size / 2, top, size, size, name, "icon")

    def add_seg(self, x1: float, y1: float, x2: float, y2: float, name: str) -> None:
        if abs(x1 - x2) < 0.5 and abs(y1 - y2) < 0.5:
            return
        self.segments.append((x1, y1, x2, y2, name))

    def poly(self, points: list[tuple[float, float]], *, dashed: bool = False, marked: bool = True, name: str = "edge") -> None:
        self.add(poly(points, dashed=dashed, marked=marked))
        for i in range(len(points) - 1):
            self.add_seg(*points[i], *points[i + 1], f"{name}:{i}")

    def arrow(self, x1: float, y1: float, x2: float, y2: float, *, dashed: bool = False, name: str = "edge") -> None:
        self.add(arrow(x1, y1, x2, y2, dashed=dashed))
        self.add_seg(x1, y1, x2, y2, name)

    def pill_at(self, x: float, y: float, text: str, container: str = "") -> None:
        self.add(pill(x, y, text))
        w = max(56, 8.2 * len(text) + 22)
        self.box(x - w / 2, y - 11, w, 22, f"pill:{text}", "pill", container=container)

    def node_at(self, x: float, y: float, icon: str, name: str, cap: str, size: float = ICON, cap2: str = "", container: str = "") -> None:
        self.add(node(x, y, icon, name, cap, size=size, cap2=cap2))
        self.icon(x, _icon_top(y, size), size, f"icon:{name}")
        if container:
            self.membership[f"icon:{name}"] = container
        self.text(x, y + 18, name, 18, bold=True, anchor="middle", name=f"name:{name}", container=container)
        if cap:
            self.text(x, y + 40, cap, 16, anchor="middle", name=f"cap:{name}", container=container)
        if cap2:
            self.text(x, y + 56, cap2, 16, anchor="middle", name=f"cap2:{name}", container=container)

    def satellite_at(self, x: float, y: float, icon: str, name: str, cap: str, size: float = 26, label_side: str = "below", name_size: int = 14, container: str = "") -> None:
        self.add(satellite(x, y, icon, name, cap, size=size, label_side=label_side, name_size=name_size))
        self.icon(x, y - size / 2, size, f"sat-icon:{name}")
        if container:
            self.membership[f"sat-icon:{name}"] = container
        if label_side == "below":
            self.text(x, y + size / 2 + 16, name, name_size, bold=True, anchor="middle", name=f"sat:{name}", container=container)
            self.text(x, y + size / 2 + 32, cap, 13, anchor="middle", name=f"sat-cap:{name}", container=container)
        elif label_side == "right":
            tx = x + size / 2 + 14
            self.text(tx, y + 5, name, 14, bold=True, anchor="start", name=f"sat:{name}", container=container)
            self.text(tx, y + 22, cap, 13, anchor="start", name=f"sat-cap:{name}", container=container)

    def grok_at(self, x: float, y: float, name: str, container: str = "") -> None:
        self.add(grok_avatar(x, y, name, ""))
        self.box(x - 48, y - 80, 96, 96, "icon:grok", "icon", container=container)
        self.text(x, y + 36, name, 18, bold=True, anchor="middle", name="name:grok", container=container)

    def check(self) -> list[str]:
        hits: list[str] = []
        for i, s1 in enumerate(self.segments):
            for s2 in self.segments[i + 1 :]:
                if _polyline_id(s1[4]) == _polyline_id(s2[4]) and _share_endpoint(s1, s2):
                    continue  # L-join on the same polyline
                if _proper_intersect(s1, s2) or _near_miss_orthogonal(s1, s2):
                    hits.append(f"polylines {_polyline_id(s1[4])} × {_polyline_id(s2[4])} ({s1[4]} / {s2[4]})")
        for s in self.segments:
            for b in self.boxes:
                if _seg_clip_len(s, b) > CLIP_HIT:
                    hits.append(f"line {s[4]} through {b[5]} {b[4]}")
        skip = ("group:", "title", "unused", "agent-events", "k3s-sub", "sg-ports")
        for i, b1 in enumerate(self.boxes):
            if b1[5] not in {"text", "pill", "icon"}:
                continue
            if any(b1[4].startswith(s) for s in skip):
                continue
            for b2 in self.boxes[i + 1 :]:
                if b2[5] not in {"text", "pill", "icon"}:
                    continue
                if any(b2[4].startswith(s) for s in skip):
                    continue
                ox = _ranges_overlap(b1[0], b1[0] + b1[2], b2[0], b2[0] + b2[2])
                oy = _ranges_overlap(b1[1], b1[1] + b1[3], b2[1], b2[1] + b2[3])
                if ox and oy and (ox[1] - ox[0]) > 8 and (oy[1] - oy[0]) > 6:
                    hits.append(f"bbox {b1[5]} {b1[4]} × {b2[5]} {b2[4]}")
        m = self.margin
        for b in self.boxes:
            if b[5] not in {"text", "pill", "icon"}:
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
        return hits


def build() -> str:
    svg, _violations = build_scene()
    return svg


def build_scene() -> tuple[str, list[str]]:
    W, H = 2100, 1420
    scene = Scene(W, H)

    # Title band with a real top margin so the 36px title is not clipped.
    aws_icon = 40
    tf_x, deploy_x, op_y = 86, 236, 118
    acct_x, acct_y, acct_w, acct_h = 400, 78, 1080, 96
    s3_x, ssm_x, secrets_x, param_x, iam_x, cw_x = 490, 640, 800, 980, 1160, 1335
    acct_node_y = 118
    acct_bot = acct_y + acct_h

    vpc_x, vpc_y, vpc_w, vpc_h = 28, 204, 1520, 1000
    bot_x, bot_y, bot_w, bot_h = 1572, 204, 500, 1000
    col_bottom = vpc_y + vpc_h

    subnet_x, subnet_y = vpc_x + 10, vpc_y + 36
    subnet_w, subnet_h = vpc_w - 24, vpc_h - 50
    sg_x, sg_y = subnet_x + 10, subnet_y + 34
    sg_w, sg_h = subnet_w - 20, subnet_h - 46

    nested_y = sg_y + 44
    k3s_x, k3s_w, k3s_opt_h = sg_x + 12, 268, 68
    compose_x = sg_x + 12
    compose_y = nested_y + k3s_opt_h + 8
    compose_w = sg_w - 24
    compose_h = sg_y + sg_h - compose_y - 10

    inner_y = compose_y + 38
    inner_h = compose_y + compose_h - inner_y - 10
    agents_x, agents_w = compose_x + 10, 318
    app_x = agents_x + agents_w + 72
    app_w = compose_x + compose_w - 12 - app_x

    # Two vertical alleys between Agents and App. Red uses the left alley;
    # Blue uses the right. Nothing else is allowed on these x's.
    alley_red = agents_x + agents_w + 16
    alley_blue = app_x - 16
    k3s_cx = agents_x + agents_w / 2

    # Unique y-lanes. Payments / faults / health sit ABOVE the service
    # icons so Redis + scrape verticals never meet them. Pills sit off the
    # shafts (above each bus, below the request arrows).
    pay_y = inner_y + 78
    faults_y = inner_y + 122
    health_y = inner_y + 166
    r_svc = inner_y + 268
    r_db = r_svc + 148
    r_obs = r_db + 128
    graf_y = inner_y + inner_h - 46
    promql_y = r_obs + 88

    tg_x = app_x + 50
    gw_x = app_x + 155
    os_x = app_x + 310
    ps_x = app_x + 480
    rd_x, pg_x = os_x - 88, os_x + 88
    br_x = app_x + app_w - 120
    am_x = br_x - 175
    prom_x = am_x - 165
    graf_x = ps_x
    scrape_x = prom_x
    br_y = r_obs

    igw_x, igw_y = vpc_x + vpc_w, vpc_y + 52
    bot_cx = bot_x + bot_w / 2
    bot_avatar_y = bot_y + 150
    bot_row_y = bot_avatar_y + 380
    gh_x, ping_x = bot_cx - 130, bot_cx + 130

    scene.add(f'''<?xml version="1.0" encoding="UTF-8"?>
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
  <text x="{W / 2:.0f}" y="64" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
''')
    scene.text(W / 2, 64, "How ResilienceOps + AI Incident Diagnosis works", 36, bold=True, anchor="middle", name="title")

    scene.add(group(acct_x, acct_y, acct_w, acct_h, "AWS account", style="account"))
    scene.container("account", acct_x, acct_y, acct_w, acct_h)
    scene.text(acct_x + 24, acct_y + 26, "AWS account", 17, bold=True, name="group:account", container="account")
    scene.add(group(vpc_x, vpc_y, vpc_w, vpc_h, "VPC  sre-enterprise-vpc", icon="aws-vpc", style="vpc"))
    scene.container("vpc", vpc_x, vpc_y, vpc_w, vpc_h)
    scene.text(vpc_x + 42, vpc_y + 26, "VPC  sre-enterprise-vpc", 17, bold=True, name="group:vpc", container="vpc")
    scene.add(group(subnet_x, subnet_y, subnet_w, subnet_h, "public_ingress  10.0.1.0/24  ·  one EC2 host", icon="aws-subnet-public", style="public_subnet"))
    scene.container("subnet", subnet_x, subnet_y, subnet_w, subnet_h)
    scene.text(subnet_x + 42, subnet_y + 26, "public_ingress  10.0.1.0/24  ·  one EC2 host", 17, bold=True, name="group:subnet", container="subnet")
    scene.add(group(sg_x, sg_y, sg_w, sg_h, "SG  ingress + internal  ·  :3000 / :8000", icon="aws-sg", style="sg"))
    scene.container("sg", sg_x, sg_y, sg_w, sg_h)
    scene.text(sg_x + 42, sg_y + 26, "SG  ingress + internal  ·  :3000 / :8000", 15, bold=True, name="group:sg", container="sg")
    scene.add(group(k3s_x, nested_y, k3s_w, k3s_opt_h, "k3s (optional)", icon="k3s", style="optional"))
    scene.container("k3s", k3s_x, nested_y, k3s_w, k3s_opt_h)
    scene.text(k3s_x + 42, nested_y + 26, "k3s (optional)", 17, bold=True, name="group:k3s", container="k3s")
    scene.add(group(compose_x, compose_y, compose_w, compose_h, "Docker Compose on this host", icon="docker"))
    scene.container("compose", compose_x, compose_y, compose_w, compose_h)
    scene.text(compose_x + 42, compose_y + 26, "Docker Compose on this host", 17, bold=True, name="group:compose", container="compose")
    scene.add(group(agents_x, inner_y, agents_w, inner_h, "Agents (--profile agents)"))
    scene.container("agents", agents_x, inner_y, agents_w, inner_h)
    scene.text(agents_x + 24, inner_y + 26, "Agents (--profile agents)", 17, bold=True, name="group:agents", container="agents")
    scene.add(group(app_x, inner_y, app_w, inner_h, "App + observability (default)"))
    scene.container("app", app_x, inner_y, app_w, inner_h)
    scene.text(app_x + 24, inner_y + 26, "App + observability (default)", 17, bold=True, name="group:app", container="app")
    scene.add(group(bot_x, bot_y, bot_w, bot_h, "Grok Bot (external)"))
    scene.container("grok", bot_x, bot_y, bot_w, bot_h)
    scene.text(bot_x + 24, bot_y + 26, "Grok Bot (external)", 17, bold=True, name="group:grok", container="grok")

    scene.add(
        f'  <text x="{k3s_x + 42:.0f}" y="{nested_y + 50:.0f}" class="cap">'
        "deploy_k8s_sandbox.py</text>"
    )
    scene.text(k3s_x + 42, nested_y + 50, "deploy_k8s_sandbox.py", 16, name="k3s-sub", container="k3s")
    scene.add(
        f'  <text x="{agents_x + 16:.0f}" y="{inner_y + 46:.0f}" class="cap">'
        "POST /api/agent-events · jsonl</text>"
    )
    scene.text(agents_x + 16, inner_y + 46, "POST /api/agent-events · jsonl", 16, name="agent-events", container="agents")
    scene.add(
        f'  <text x="{vpc_x + vpc_w - 18:.0f}" y="{vpc_y + 26:.0f}" text-anchor="end" '
        f'class="cap">app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24 · unused</text>'
    )
    scene.text(
        vpc_x + vpc_w - 18, vpc_y + 26,
        "app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24 · unused",
        16, anchor="end", name="unused-cidrs", container="vpc",
    )

    scene.node_at(tf_x, op_y, "terraform", "Terraform", "optional AWS", size=aws_icon)
    scene.node_at(deploy_x, op_y, "document", "deploy_remote.py", "operator", size=aws_icon)
    scene.satellite_at(s3_x, acct_node_y, "aws-s3", "S3", "deploy → host", container="account")
    scene.satellite_at(ssm_x, acct_node_y, "aws-ssm", "SSM", "send_command", container="account")
    scene.satellite_at(secrets_x, acct_node_y, "document", "put_lab_secrets.py", "laptop → Param", name_size=11, container="account")
    scene.satellite_at(param_x, acct_node_y, "aws-ssm", "Param Store", "secrets → .env", container="account")
    scene.satellite_at(iam_x, acct_node_y, "aws-iam", "IAM", "role + profile", container="account")
    scene.satellite_at(cw_x, acct_node_y, "aws-cloudwatch", "CW Logs", "agents → CW", container="account")
    scene.satellite_at(igw_x, igw_y, "aws-igw", "IGW", "public RT only", size=28, label_side="right")

    # Red sits on the faults lane (short hop into the alley). Blue sits on
    # the observability row so the query is a straight run and health uses
    # a dedicated riser in alley_blue.
    red_y = faults_y + ICON / 2 + 8
    blue_y = r_obs
    scene.node_at(k3s_cx, red_y, "person-red", "Red Team", "Injects faults", container="agents")
    scene.node_at(k3s_cx, blue_y, "person-blue", "Blue Team", "Detects and resets", container="agents")
    scene.node_at(tg_x, r_svc, "traffic", "Traffic", "Live load", container="app")
    scene.node_at(gw_x, r_svc, "fastapi", "api-gw", "Gateway", container="app")
    scene.node_at(os_x, r_svc, "fastapi", "order-service", "Orders", container="app")
    scene.node_at(ps_x, r_svc, "fastapi", "payment-service", "Payments", container="app")
    scene.node_at(rd_x, r_db, "redis", "Redis", "order-service cache", container="app")
    scene.node_at(pg_x, r_db, "postgresql", "PostgreSQL", "orders_db", container="app")
    scene.node_at(prom_x, r_obs, "prometheus", "Prometheus", "", container="app")
    scene.node_at(am_x, r_obs, "alertmanager", "Alertmanager", "Groups alerts", container="app")
    scene.node_at(br_x, br_y, "document", "incident-bridge", "PromQL · agent jsonl", cap2="(Compose agents)", container="app")
    scene.node_at(graf_x, graf_y, "grafana", "Grafana", "", size=52, container="app")
    scene.grok_at(bot_cx, bot_avatar_y, "AI Incident Diagnosis", container="grok")
    scene.node_at(gh_x, bot_row_y, "github", "GitHub issue", "label: incident", container="grok")
    scene.node_at(ping_x, bot_row_y, "bell", "Owner ping", "Firing critical", container="grok")

    svc_ic = _ic(r_svc)
    red_ic = _ic(red_y)
    blue_ic = _ic(blue_y)
    red_right = k3s_cx + ICON / 2 + 14
    blue_right = k3s_cx + ICON / 2 + 14
    icon_top_svc = _icon_top(r_svc)
    db_top = _icon_top(r_db)
    prom_top = _icon_top(r_obs)
    graf_top = _icon_top(graf_y, 52)
    tf_bot = op_y + 48  # below Terraform cap bbox
    deploy_right = deploy_x + _tw("deploy_remote.py", 18, True) / 2 + 8

    # 1. Terraform L-routes just above the VPC stroke and lands right of
    # the VPC title — never into the account strip.
    vpc_title_end = vpc_x + 42 + _tw("VPC  sre-enterprise-vpc", 17, True) + 16
    tf_land_x = max(vpc_title_end, tf_x + 40)
    scene.poly([
        (tf_x, tf_bot),
        (tf_x, vpc_y - 10),
        (tf_land_x, vpc_y - 10),
        (tf_land_x, vpc_y),
    ], name="tf-vpc")

    # 1b. deploy_remote.py lands on the AWS-account LEFT BORDER below the
    # "AWS account" caption, then hops to S3. S3→host and SSM→host drop
    # from the account BOTTOM BORDER (clear of satellite captions) onto
    # the VPC stroke.
    acct_title_bottom = acct_y + 26 + 8
    entry_y = max(acct_title_bottom + 12, acct_node_y)
    deploy_s3_pts = [(deploy_right, op_y)]
    if abs(op_y - entry_y) > 1:
        deploy_s3_pts.append((deploy_right, entry_y))
    deploy_s3_pts.extend([(acct_x, entry_y), (s3_x - 16, entry_y)])
    scene.poly(deploy_s3_pts, name="deploy-s3")
    scene.arrow(s3_x, acct_bot, s3_x, vpc_y, name="s3-host")
    scene.arrow(ssm_x, acct_bot, ssm_x, vpc_y, name="ssm-host")

    # 1c. put_lab_secrets.py → Param Store. Short hop between adjacent icons.
    scene.arrow(secrets_x + 16, acct_node_y, param_x - 16, acct_node_y, name="secrets-param")

    # 2–4. Request path at icon centers. Pills sit ABOVE the shafts (and
    # above the icons) so they can be wider than the inter-icon gap.
    scene.arrow(tg_x + 36, svc_ic, gw_x - 36, svc_ic, name="req-gw")
    scene.arrow(gw_x + 36, svc_ic, os_x - 36, svc_ic, name="req-os")
    scene.arrow(os_x + 36, svc_ic, ps_x - 36, svc_ic, name="req-ps")
    req_pill_y = icon_top_svc - 16
    scene.pill_at((tg_x + gw_x) / 2, req_pill_y, "requests")
    scene.pill_at((gw_x + os_x) / 2, req_pill_y, "/api/orders")
    # Sit to the right of the order-service health tick so the tick
    # cannot run through this (wide) pill.
    scene.pill_at(os_x + (ps_x - os_x) * 0.62, req_pill_y, "POST /payments")

    # 5. /api/payments U-turn on its own lane above faults. Ticks stop
    # before the faults bus.
    scene.poly([(gw_x, pay_y), (ps_x, pay_y)], marked=False, name="pay-bus")
    scene.arrow(gw_x, pay_y, gw_x, faults_y - 10, name="pay-tick-gw")
    scene.arrow(ps_x, pay_y, ps_x, faults_y - 10, name="pay-tick-ps")
    scene.pill_at((gw_x + os_x) / 2, pay_y - 20, "/api/payments")

    # 8. Faults lane. The long horizontal lives only in the app column
    # (x >= app_x) so it cannot share an x with Blue's alley riser.
    # Red reaches that bus via a flyover ABOVE pay_y.
    fault_tick_x_os, fault_tick_x_ps = os_x - 22, ps_x - 22
    red_fly_y = inner_y + 48
    fault_join_x = app_x + 10
    scene.poly([
        (red_right, red_ic),
        (alley_red, red_ic),
        (alley_red, red_fly_y),
        (fault_join_x, red_fly_y),
        (fault_join_x, faults_y),
        (fault_tick_x_ps, faults_y),
    ], marked=False, name="fault-bus")
    scene.arrow(fault_tick_x_os, faults_y, fault_tick_x_os, health_y - 10, name="fault-os")
    scene.arrow(fault_tick_x_ps, faults_y, fault_tick_x_ps, health_y - 10, name="fault-ps")
    scene.pill_at((os_x + ps_x) / 2, faults_y - 20, "faults")

    # 9. Health/reset lane. Blue riser stays in alley_blue (between
    # Agents and App), which the fault horizontal never occupies.
    h_gw, h_os, h_ps = gw_x + 22, os_x + 22, ps_x + 22
    scene.poly([
        (blue_right, blue_ic),
        (alley_blue, blue_ic),
        (alley_blue, health_y),
        (h_ps, health_y),
    ], marked=False, name="health-bus")
    scene.arrow(h_gw, health_y, h_gw, icon_top_svc - 2, name="health-gw")
    scene.arrow(h_os, health_y, h_os, icon_top_svc - 2, name="health-os")
    scene.arrow(h_ps, health_y, h_ps, icon_top_svc - 2, name="health-ps")
    scene.pill_at(gw_x - 10, health_y - 20, "health ×3")
    scene.pill_at((os_x + ps_x) / 2, health_y - 20, "reset ×2")

    # 6–7. order-service → Redis / Postgres. Stem drops from below the
    # service caption, then forks. Entirely under the health lane.
    os_bot = r_svc + 52
    fork_y = os_bot + 18
    scene.poly([(os_x, os_bot), (os_x, fork_y), (rd_x, fork_y), (rd_x, db_top)], name="os-redis")
    scene.poly([(os_x, fork_y), (pg_x, fork_y), (pg_x, db_top)], name="os-pg")

    # 10. Blue → Prometheus. Shares the Blue riser; branches right at
    # icon-center y of the observability row (below Redis captions).
    scene.arrow(alley_blue, blue_ic, prom_x - 48, blue_ic, name="blue-query")
    scene.pill_at(rd_x, blue_ic - 22, "query")

    # 11. Scrape: one short orthogonal from the service row, down a
    # dedicated column (scrape_x) that is not prom_x (so it cannot share
    # a shaft with Prom→Grafana).
    scene.poly([
        (ps_x + 36, svc_ic),
        (scrape_x, svc_ic),
        (scrape_x, prom_top),
    ], name="scrape")
    scene.pill_at(scrape_x + 78, svc_ic - 22, "3 scrape jobs")

    # 12–13. Observability row.
    scene.arrow(prom_x + 44, blue_ic, am_x - 44, blue_ic, name="prom-am")
    scene.pill_at((prom_x + am_x) / 2, blue_ic - 22, "alerts")
    scene.arrow(am_x + 44, blue_ic, br_x - 44, blue_ic, name="am-br")
    scene.pill_at((am_x + br_x) / 2, blue_ic - 22, "webhook")

    # 14. Prometheus → Grafana. Grafana sits under payment-service so the
    # PromQL U-turn (right of Prometheus) cannot run through it.
    graf_shaft_y0 = r_obs + 28
    graf_run_y = graf_top - 18
    scene.poly([
        (prom_x, graf_shaft_y0),
        (prom_x, graf_run_y),
        (graf_x, graf_run_y),
        (graf_x, graf_top),
    ], name="prom-graf")
    scene.pill_at(graf_x - 8, graf_run_y - 20, "reads")

    # 15. PromQL, dashed, under the bridge caption. Column is to the RIGHT
    # of Prometheus so it does not share the Prom→Grafana shaft.
    scene.poly([
        (br_x, r_obs + 72),
        (br_x, promql_y),
        (prom_x + 52, promql_y),
        (prom_x + 52, r_obs + 34),
    ], dashed=True, name="promql")
    scene.pill_at((am_x + br_x) / 2, promql_y + 20, "PromQL")

    # 16. Bridge → Grok via the VPC–Grok gutter, well below the IGW labels.
    hex_cy = bot_avatar_y - 32
    gutter = vpc_x + vpc_w + 56
    scene.poly([
        (br_x + 40, blue_ic),
        (gutter, blue_ic),
        (gutter, hex_cy),
        (bot_cx - 52, hex_cy),
    ], name="br-grok")
    scene.pill_at(bot_cx - 110, hex_cy - 26, "enriched JSON")

    # 17–18. Grok → GitHub / ping.
    out_y = bot_avatar_y + 78
    fork_y_g = out_y + 40
    gh_top = _icon_top(bot_row_y)
    scene.poly([(bot_cx, out_y), (bot_cx, fork_y_g)], marked=False, name="grok-stem")
    scene.poly([(bot_cx, fork_y_g), (gh_x, fork_y_g), (gh_x, gh_top)], name="grok-gh")
    scene.poly([(bot_cx, fork_y_g), (ping_x, fork_y_g), (ping_x, gh_top)], name="grok-ping")
    scene.pill_at(bot_cx, fork_y_g + 24, "diagnose")

    gate_y = col_bottom + 20
    gate_h = 62
    gate_x = CANVAS_MARGIN
    gate_w = W - 2 * CANVAS_MARGIN
    scene.add(
        f'  <rect x="{gate_x:.0f}" y="{gate_y:.0f}" width="{gate_w:.0f}" height="{gate_h:.0f}" rx="16" fill="#FFFFFF" '
        f'stroke="#D1D5DB" stroke-dasharray="7 6"/>'
    )
    scene.add(
        f'  <text x="{W / 2:.0f}" y="{gate_y + 28:.0f}" text-anchor="middle" class="gate">'
        "The bot has no control path into the lab: it only receives webhooks and writes GitHub issues.</text>"
    )
    scene.text(W / 2, gate_y + 28, "The bot has no control path into the lab: it only receives webhooks and writes GitHub issues.", 18, bold=True, anchor="middle", name="gate-1")
    scene.add(
        f'  <text x="{W / 2:.0f}" y="{gate_y + 50:.0f}" text-anchor="middle" class="gate-sub">'
        "AWS/EC2 is optional: docker compose up runs the same lab (agents need --profile agents). "
        "The bridge needs outbound HTTPS to the bot; agents also call Anthropic.</text>"
    )
    scene.text(W / 2, gate_y + 50, "AWS/EC2 is optional: docker compose up runs the same lab (agents need --profile agents). The bridge needs outbound HTTPS to the bot; agents also call Anthropic.", 16, anchor="middle", name="gate-2")
    card_y = gate_y + gate_h + 12
    card_w, card_h = 640, 64
    card_gap = 20
    card_x0 = CANVAS_MARGIN
    card_x1 = card_x0 + card_w + card_gap
    card_x2 = card_x1 + card_w + card_gap

    def card2(n: int, x: float, line1: str, line2: str) -> str:
        scene.text(x + 52, card_y + 26, line1, 17, name=f"card{n}-1")
        scene.text(x + 52, card_y + 50, line2, 17, name=f"card{n}-2")
        return f"""  <g transform="translate({x:.0f},{card_y:.0f})">
    <rect width="{card_w:.0f}" height="{card_h:.0f}" rx="14" fill="#FFF7ED" stroke="#FDBA74"/>
    <text x="24" y="26" class="card-n">{n}.</text>
    <text x="52" y="26" class="card-t">{line1}</text>
    <text x="52" y="50" class="card-t">{line2}</text>
  </g>"""

    scene.add(card2(
        1, card_x0,
        "Held fault (FAULT_HOLD_SECONDS, default 120)",
        "or a real outage trips a Prometheus alert rule.",
    ))
    scene.add(card2(2, card_x1, "Bridge adds PromQL + jsonl and posts", "enriched JSON to the bot."))
    scene.add(card2(3, card_x2, "Bot diagnoses and files or", "updates a GitHub issue."))
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
        for item in violations[:60]:
            print(f"  {item}")
        if len(violations) > 60:
            print(f"  ... {len(violations) - 60} more")
        return 1
    print("geometry: 0 violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
