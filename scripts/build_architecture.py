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
INC_ORANGE = "#EA580C"

# Native sizes. README shows the figure at 950 px wide; 13 px effective
# at that width on a 1600 px canvas means ≥21.9 px native.
ICON = 52
NAME_PX = 26
CAP_PX = 22
GROUP_PX = 22
TITLE_PX = 40
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
            f'    <text class="name" y="18" text-anchor="middle">{name}</text>\n'
            f'    <text class="name" y="42" text-anchor="middle">{name2}</text>\n'
        )
        cap_y, cap2_y = 66, 90
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


def grok_avatar(x: float, y: float, name: str, cap: str) -> str:
    path = _rounded_hexagon_path()
    cap_svg = (
        f'    <text class="cap" y="70" text-anchor="middle">{cap}</text>\n' if cap else ""
    )
    return f"""  <g transform="translate({x:.0f},{y:.0f})">
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
            f'x="{x + 12:.0f}" y="{y + 8:.0f}" width="22" height="22"/>\n'
        )
        text_x = x + 40
    return (
        f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="{pal["rx"]}" fill="{pal["fill"]}" stroke="{pal["stroke"]}" '
        f'stroke-width="{pal["sw"]}"{pal["dash"]}/>\n'
        f"{icon_svg}"
        f'  <text x="{text_x:.0f}" y="{y + 28:.0f}" class="{pal["cls"]}">{label}</text>'
    )


def _stroke(inc: bool, dashed: bool, thin: bool = False) -> tuple[str, str, str]:
    if inc and thin:
        cls = "arrow-inc-thin"
    elif inc:
        cls = "arrow-inc"
    else:
        cls = "arrow"
    mk = "arr-inc" if inc else "arr"
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
) -> str:
    cls, mk, dash = _stroke(inc, dashed, thin=thin)
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
) -> str:
    pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in points)
    cls, mk, dash = _stroke(inc, dashed, thin=thin)
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

    def add_seg(self, x1: float, y1: float, x2: float, y2: float, name: str) -> None:
        if abs(x1 - x2) < 0.5 and abs(y1 - y2) < 0.5:
            return
        self.segments.append((x1, y1, x2, y2, name))

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
        name: str = "edge",
    ) -> None:
        self.add(poly(points, dashed=dashed, marked=marked, inc=inc, thin=thin))
        self._mark(name, marked)
        for i in range(len(points) - 1):
            self.add_seg(*points[i], *points[i + 1], f"{name}:{i}")

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
        name: str = "edge",
    ) -> None:
        self.add(arrow(x1, y1, x2, y2, dashed=dashed, inc=inc, thin=thin))
        self._mark(name, True)
        self.add_seg(x1, y1, x2, y2, name)

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
            self.text(x, y + 18, name, name_size, bold=True, anchor="middle", name=f"name:{name}", container=container)
            self.text(x, y + 42, name2, name_size, bold=True, anchor="middle", name=f"name2:{name}", container=container)
            cap_y, cap2_y = y + 66, y + 90
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

    def badge(self, x: float, y: float, n: int, container: str = "") -> None:
        r = 15
        self.add(
            f'  <g transform="translate({x:.0f},{y:.0f})">'
            f'<circle r="{r}" fill="{INC_ORANGE}" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text text-anchor="middle" dy="7" class="badge">{n}</text></g>'
        )
        self.box(x - r, y - r, 2 * r, 2 * r, f"badge:{n}", "badge", container=container)
        self.fonts.append((f"badge:{n}", 22))

    def check(self) -> list[str]:
        hits: list[str] = []
        for i, s1 in enumerate(self.segments):
            for s2 in self.segments[i + 1 :]:
                if _polyline_id(s1[4]) == _polyline_id(s2[4]) and _share_endpoint(s1, s2):
                    continue
                if _proper_intersect(s1, s2) or _near_miss_orthogonal(s1, s2):
                    hits.append(
                        f"polylines {_polyline_id(s1[4])} × {_polyline_id(s2[4])} "
                        f"({s1[4]} {s1[0]:.0f},{s1[1]:.0f}-{s1[2]:.0f},{s1[3]:.0f} / "
                        f"{s2[4]} {s2[0]:.0f},{s2[1]:.0f}-{s2[2]:.0f},{s2[3]:.0f})"
                    )
        halo_skip = (
            "group:",
            "title",
            "host-title",
            "host-sg",
            "agents-cap",
            "k3s-sub",
            "legend",
            "foot",
        )
        for s in self.segments:
            for b in self.boxes:
                kind = b[5]
                if kind == "text":
                    if any(b[4].startswith(p) for p in halo_skip):
                        continue
                    else:
                        inf = (
                            b[0] - TEXT_CLEARANCE,
                            b[1] - TEXT_CLEARANCE,
                            b[2] + 2 * TEXT_CLEARANCE,
                            b[3] + 2 * TEXT_CLEARANCE,
                        )
                        if _seg_clip_len(s, inf) > 0.5:
                            hits.append(f"line {s[4]} near text {b[4]} (<{TEXT_CLEARANCE:.0f}px)")
                elif kind in {"icon", "badge"}:
                    if _seg_clip_len(s, b) > CLIP_HIT:
                        hits.append(f"line {s[4]} through {kind} {b[4]}")
        skip = ("group:", "title", "k3s-sub", "foot", "legend", "host-title", "host-sg")
        for i, b1 in enumerate(self.boxes):
            if b1[5] not in {"text", "icon", "badge"}:
                continue
            if any(b1[4].startswith(s) for s in skip):
                continue
            for b2 in self.boxes[i + 1 :]:
                if b2[5] not in {"text", "icon", "badge"}:
                    continue
                if any(b2[4].startswith(s) for s in skip):
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
                # Legend / title / footer must not sit on a group stroke.
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
    W, H = 1600, 1360
    scene = Scene(W, H)

    dep_y, dep_h = 108, 200
    lap_x, lap_w = 24, 776
    aws_x, aws_w = 812, 764
    sat_y = 192
    fly_y = 160
    tf_x, sec_x, dep_x = 100, 310, 550
    s3_x, ssm_x, par_x = 910, 1130, 1370
    drop_x = 1020

    host_x, host_y, host_w, host_h = 24, 328, 1200, 820
    bot_x, bot_y, bot_w, bot_h = 1236, 328, 332, 800

    compose_x, compose_y = 36, 368
    compose_w, compose_h = 1186, 672
    k3s_x, k3s_y, k3s_w, k3s_h = 36, 1056, 1186, 76

    agents_x, agents_y, agents_w, agents_h = 48, 424, 280, 560
    red_x, red_y = 188, 670
    blue_x, blue_y = 188, 850

    tg_x, gw_x, req_y = 370, 555, 500
    os_x, os_y = 440, 670
    ps_x, ps_y = 700, 670
    prom_x, am_x = 910, 1115
    graf_x, graf_y = 910, 820
    br_x, br_y = 1115, 820
    rd_x, pg_x, db_y = 440, 600, 930

    bot_cx = bot_x + bot_w / 2
    bot_av_y = 500
    gh_x, ping_x, gh_y, ping_y = 1345, 1488, 760, 760

    scene.add(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"
     aria-label="How ResilienceOps plus AI Incident Diagnosis works">
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
      .arrow-inc {{ stroke: {INC_ORANGE}; stroke-width: 3.4; fill: none; }}
      .arrow-inc-thin {{ stroke: {INC_ORANGE}; stroke-width: 2.0; fill: none; }}
      .arrow-inc-thin {{ stroke: {INC_ORANGE}; stroke-width: 2.0; fill: none; }}
    </style>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#9CA3AF"/>
    </marker>
    <marker id="arr-inc" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{INC_ORANGE}"/>
    </marker>
{symbols()}
  </defs>
  <rect width="{W}" height="{H}" fill="#FFFFFF"/>
    <text x="{W / 2:.0f}" y="72" text-anchor="middle" class="title">How ResilienceOps + AI Incident Diagnosis works</text>
''')
    scene.text(W / 2, 72, "How ResilienceOps + AI Incident Diagnosis works", TITLE_PX, bold=True, anchor="middle", name="title")

    # Deploy band.
    scene.add(group(lap_x, dep_y, lap_w, dep_h, "Deploy (optional AWS) · laptop", style="account"))
    scene.container("laptop", lap_x, dep_y, lap_w, dep_h)
    scene.text(lap_x + 18, dep_y + 28, "Deploy (optional AWS) · laptop", GROUP_PX, bold=True, name="group:laptop", container="laptop")
    scene.add(group(aws_x, dep_y, aws_w, dep_h, "AWS", icon="aws-s3", style="account"))
    scene.container("aws", aws_x, dep_y, aws_w, dep_h)
    scene.text(aws_x + 40, dep_y + 28, "AWS", GROUP_PX, bold=True, name="group:aws", container="aws")

    scene.satellite_at(tf_x, sat_y, "terraform", "Terraform", "IaC", container="laptop")
    scene.satellite_at(sec_x, sat_y, "document", "put_lab_secrets.py", "laptop", name_size=22, container="laptop")
    scene.satellite_at(dep_x, sat_y, "document", "deploy_remote.py", "operator", container="laptop")
    scene.satellite_at(s3_x, sat_y, "aws-s3", "S3", "zip → host", container="aws")
    scene.satellite_at(ssm_x, sat_y, "aws-ssm", "SSM", "send_command", container="aws")
    scene.satellite_at(par_x, sat_y, "aws-ssm", "Param Store", "secrets → .env", container="aws")

    # Host + bot columns. Two-line EC2 title so the AWS→host drop misses the header text.
    host_title = "EC2 host · VPC 10.0.0.0/16 · public subnet"
    host_sg = "SG :3000/:8000 from allowed_cidr"
    scene.add(group(host_x, host_y, host_w, host_h, host_title, icon="aws-ec2", style="host"))
    scene.container("host", host_x, host_y, host_w, host_h)
    scene.text(host_x + 40, host_y + 28, host_title, GROUP_PX, bold=True, name="host-title", container="host")
    scene.add(f'  <text x="{host_x + 700:.0f}" y="{host_y + 28:.0f}" class="cap">{host_sg}</text>')
    scene.text(host_x + 700, host_y + 28, host_sg, CAP_PX, name="host-sg", container="host")
    scene.add(group(bot_x, bot_y, bot_w, bot_h, "External", style="bot"))
    scene.container("bot", bot_x, bot_y, bot_w, bot_h)
    scene.text(bot_x + 18, bot_y + 28, "External", GROUP_PX, bold=True, name="group:bot", container="bot")

    scene.add(group(compose_x, compose_y, compose_w, compose_h, "Lab (Docker Compose)", icon="docker"))
    scene.container("compose", compose_x, compose_y, compose_w, compose_h)
    scene.text(compose_x + 40, compose_y + 28, "Lab (Docker Compose)", GROUP_PX, bold=True, name="group:compose", container="compose")

    scene.add(group(agents_x, agents_y, agents_w, agents_h, "Agents", style=None))
    scene.container("agents", agents_x, agents_y, agents_w, agents_h)
    scene.text(agents_x + 14, agents_y + 26, "Agents", GROUP_PX, bold=True, name="group:agents", container="agents")
    scene.add(
        f'  <text x="{agents_x + 14:.0f}" y="{agents_y + 50:.0f}" class="cap">--profile agents</text>'
    )
    scene.text(agents_x + 14, agents_y + 50, "--profile agents", CAP_PX, name="agents-cap", container="agents")

    k3s_title = "k3s sandbox (optional)"
    k3s_sub = "Optional: runs orchestrator.py in one sandbox pod"
    scene.add(group(k3s_x, k3s_y, k3s_w, k3s_h, k3s_title, icon="k3s", style="optional"))
    scene.container("k3s", k3s_x, k3s_y, k3s_w, k3s_h)
    scene.text(k3s_x + 40, k3s_y + 28, k3s_title, GROUP_PX, bold=True, name="group:k3s", container="k3s")
    scene.add(f'  <text x="{k3s_x + 40:.0f}" y="{k3s_y + 54:.0f}" class="cap">{k3s_sub}</text>')
    scene.text(k3s_x + 40, k3s_y + 54, k3s_sub, CAP_PX, name="k3s-sub", container="k3s")

    scene.node_at(
        red_x, red_y, "person-red", "Red Team", "faults order", cap2="+ payment", container="agents"
    )
    scene.node_at(
        blue_x,
        blue_y,
        "person-blue",
        "Blue Team",
        "health on all 3",
        cap2="reset order + payment",
        container="agents",
    )
    scene.node_at(tg_x, req_y, "traffic", "Traffic", "load", container="compose")
    scene.node_at(gw_x, req_y, "fastapi", "api-gw", "", container="compose")
    scene.node_at(os_x, os_y, "fastapi", "order-", "", name2="service", container="compose")
    scene.node_at(ps_x, ps_y, "fastapi", "payment-", "", name2="service", container="compose")
    scene.node_at(prom_x, os_y, "prometheus", "Prometheus", "pulls /metrics", container="compose")
    scene.node_at(am_x, os_y, "alertmanager", "Alert", "", name2="manager", container="compose")
    scene.node_at(br_x, br_y, "document", "incident-", "PromQL · jsonl", name2="bridge", container="compose")
    scene.node_at(rd_x, db_y, "redis", "Redis", "cache", container="compose")
    scene.node_at(pg_x, db_y, "postgresql", "PostgreSQL", "orders_db", container="compose")
    scene.node_at(graf_x, graf_y, "grafana", "Grafana", "reads Prom", size=48, container="compose")
    scene.grok_at(bot_cx, bot_av_y, "AI Incident Diagnosis", container="bot")
    scene.node_at(gh_x, gh_y, "github", "GitHub", "label: incident", name2="issue", container="bot")
    scene.node_at(ping_x, ping_y, "bell", "Owner ping", "critical", name_size=22, container="bot")

    req_ic = _ic(req_y)
    svc_ic = _ic(os_y)
    br_ic = _ic(br_y)
    db_top = _icon_top(db_y)
    graf_top = _icon_top(graf_y, 48)
    os_top = _icon_top(os_y)
    ps_top = _icon_top(ps_y)
    prom_top = _icon_top(os_y)
    red_top = _icon_top(red_y)
    sat_top = sat_y - 15
    red_right = red_x + ICON / 2 + 10
    blue_right = blue_x + ICON / 2 + 10
    os_left, os_right = os_x - ICON / 2 - 8, os_x + ICON / 2 + 8
    ps_right = ps_x + ICON / 2 + 8
    prom_left, prom_right = prom_x - ICON / 2 - 8, prom_x + ICON / 2 + 8
    am_left, am_right = am_x - ICON / 2 - 8, am_x + ICON / 2 + 8
    gw_right = gw_x + ICON / 2 + 8
    br_right = br_x + ICON / 2 + 10
    hex_cy = bot_av_y - 32
    fault_y = 434
    scrape_y = 590
    blue_mid_y = 568
    blue_fly_y = 418
    db_join_y = 742
    redis_lane = 350
    pg_lane = 600
    blue_up = 40
    health_y = 830
    os_scrape_x = os_x + 20
    gw_join_x = 800
    scrape_bus_end = 680
    scrape_stem_x = prom_x - 26
    promql_x = 1210
    br_bot_x = 1230
    ps_down_x = 750
    am_gutter = 1189
    fork_y = 640
    trunk_y = 604

    # Deploy: one bus under the AWS header, T-drops into S3 / SSM / Param, one drop into EC2.
    scene.poly([(sec_x, sat_top), (sec_x, fly_y)], marked=False, name="secrets-up")
    scene.poly([(dep_x, sat_top), (dep_x, fly_y)], marked=False, name="deploy-up")
    scene.poly([(sec_x, fly_y), (par_x, fly_y)], marked=False, name="deploy-bus")
    scene.poly([(s3_x, fly_y), (s3_x, sat_top)], name="deploy-s3")
    scene.poly([(ssm_x, fly_y), (ssm_x, sat_top)], name="deploy-ssm")
    scene.poly([(par_x, fly_y), (par_x, sat_top)], name="secrets-param")
    scene.poly([(drop_x, fly_y), (drop_x, host_y)], name="aws-host")

    # Grey request path: Traffic → api-gw.
    scene.arrow(tg_x + ICON / 2 + 8, req_ic, gw_x - ICON / 2 - 8, req_ic, name="req-gw")

    # ① Both faults leave Red upward, then T down to OS and continue to PS.
    scene.poly(
        [
            (red_x, red_top),
            (red_x, fault_y),
            (ps_down_x, fault_y),
            (ps_down_x, os_y - 20),
            (ps_right, os_y - 20),
        ],
        inc=True,
        name="fault-ps",
    )
    scene.poly([(290, fault_y), (290, os_top), (os_left, os_top)], inc=True, name="fault-os")
    scene.badge(330, 400, 1, container="compose")

    # ② Thin ticks from all 3 services into a short bus; stem along icon tops into Prometheus (pull).
    scene.poly(
        [(os_scrape_x, os_top), (os_scrape_x, scrape_y)],
        marked=False,
        inc=True,
        thin=True,
        name="scrape-os",
    )
    scene.poly(
        [(680, ps_top), (680, scrape_y)],
        marked=False,
        inc=True,
        thin=True,
        name="scrape-ps",
    )
    scene.poly(
        [(gw_right, req_ic), (640, req_ic), (640, scrape_y)],
        marked=False,
        inc=True,
        thin=True,
        name="scrape-gw",
    )
    scene.poly(
        [(os_scrape_x, scrape_y), (748, scrape_y)],
        marked=False,
        inc=True,
        thin=True,
        name="scrape-bus",
    )
    scene.poly(
        [
            (752, scrape_y),
            (scrape_stem_x, scrape_y),
            (scrape_stem_x, prom_top),
        ],
        inc=True,
        thin=True,
        name="scrape",
    )
    scene.badge(scrape_bus_end - 30, scrape_y + 22, 2, container="compose")

    # ③ Prom → AM  ④ AM → incident-bridge (right gutter, not through labels)
    scene.arrow(prom_right, svc_ic, am_left, svc_ic, inc=True, name="prom-am")
    scene.badge((prom_x + am_x) / 2, svc_ic - 24, 3, container="compose")
    scene.poly(
        [
            (am_right, svc_ic),
            (am_gutter, svc_ic),
            (am_gutter, 740),
            (am_x, 740),
            (am_x, _icon_top(br_y)),
        ],
        inc=True,
        name="am-br",
    )
    scene.badge(1189, 600, 4, container="compose")

    # ⑤ bridge → bot; dashed PromQL back to Prometheus via the right gutter
    scene.poly(
        [(br_right, 916), (br_bot_x, 916), (br_bot_x, hex_cy), (bot_cx - 52, hex_cy)],
        inc=True,
        name="br-bot",
    )
    scene.badge(bot_x + 26, hex_cy - 26, 5, container="bot")
    scene.poly(
        [
            (br_right, 780),
            (promql_x, 780),
            (promql_x, blue_mid_y),
            (prom_right, blue_mid_y),
        ],
        dashed=True,
        name="promql",
    )

    # ⑥ Short trunk below the bot label, then a clean fork to GitHub + Owner ping.
    scene.poly([(bot_cx, trunk_y), (bot_cx, fork_y)], marked=False, inc=True, name="bot-trunk")
    scene.poly([(bot_cx, fork_y), (gh_x, fork_y), (gh_x, _icon_top(gh_y))], inc=True, name="bot-gh")
    scene.poly(
        [(bot_cx, fork_y), (ping_x, fork_y), (ping_x, _icon_top(ping_y))],
        inc=True,
        name="bot-ping",
    )
    scene.badge(bot_cx - 36, (trunk_y + fork_y) / 2, 6, container="bot")

    scene.arrow(prom_x, os_y + 80, prom_x, graf_top, name="prom-graf")

    # order-service → Redis and PostgreSQL; order-service → payment-service.
    scene.poly(
        [(os_left, db_join_y), (redis_lane, db_join_y), (redis_lane, db_top), (rd_x, db_top)],
        name="os-redis",
    )
    scene.poly(
        [(os_right, db_join_y), (pg_lane, db_join_y), (pg_lane, db_top)],
        name="os-pg",
    )
    scene.arrow(os_right, os_y - 20, ps_x - ICON / 2 - 8, os_y - 20, name="os-ps")

    # Blue: one grey stub to the services column, one dashed query over the top into Prometheus.
    scene.arrow(blue_right, health_y, redis_lane - 20, health_y, name="blue-health")
    scene.poly(
        [
            (blue_x, _icon_top(blue_y)),
            (blue_up, _icon_top(blue_y)),
            (blue_up, blue_fly_y),
            (920, blue_fly_y),
            (920, prom_top),
        ],
        dashed=True,
        name="blue-query",
    )

    host_bottom = host_y + host_h
    leg_y = host_bottom + 34
    scene.add(
        f'  <line x1="36" y1="{leg_y}" x2="70" y2="{leg_y}" class="arrow-inc"/>'
        f'  <text x="80" y="{leg_y + 6}" class="legend">1–6 incident path</text>'
        f'  <line x1="300" y1="{leg_y}" x2="334" y2="{leg_y}" class="arrow"/>'
        f'  <text x="344" y="{leg_y + 6}" class="legend">supporting</text>'
        f'  <line x1="500" y1="{leg_y}" x2="544" y2="{leg_y}" class="arrow" stroke-dasharray="7 6"/>'
        f'  <text x="554" y="{leg_y + 6}" class="legend">query (PromQL)</text>'
    )
    scene.text(80, leg_y + 6, "1–6 incident path", CAP_PX, name="legend-inc")
    scene.text(344, leg_y + 6, "supporting", CAP_PX, name="legend-sup")
    scene.text(554, leg_y + 6, "query (PromQL)", CAP_PX, name="legend-q")

    iam1 = "IAM role + instance profile · CloudWatch log groups"
    iam2 = "IGW · unused subnets app_workloads 10.0.10.0/24 · data_persistence 10.0.20.0/24"
    foot_y = leg_y + 28
    scene.add(f'  <text x="{W / 2:.0f}" y="{foot_y}" text-anchor="middle" class="cap">{iam1}</text>')
    scene.add(f'  <text x="{W / 2:.0f}" y="{foot_y + 22}" text-anchor="middle" class="cap">{iam2}</text>')
    scene.text(W / 2, foot_y, iam1, CAP_PX, anchor="middle", name="foot-iam1")
    scene.text(W / 2, foot_y + 22, iam2, CAP_PX, anchor="middle", name="foot-iam2")

    f1 = "① Red faults order-service + payment-service (FAULT_HOLD_SECONDS default 120)   ② Prometheus scrapes all 3"
    f2 = "③ Alertmanager   ④ incident-bridge   ⑤ AI Incident Diagnosis   ⑥ GitHub issue (label: incident) + owner ping"
    f3 = "The bot has no control path into the lab: webhook in, GitHub issue + owner ping out."
    scene.add(f'  <text x="{W / 2:.0f}" y="{foot_y + 50}" text-anchor="middle" class="foot">{f1}</text>')
    scene.add(f'  <text x="{W / 2:.0f}" y="{foot_y + 74}" text-anchor="middle" class="foot">{f2}</text>')
    scene.add(f'  <text x="{W / 2:.0f}" y="{foot_y + 98}" text-anchor="middle" class="foot">{f3}</text>')
    scene.text(W / 2, foot_y + 50, f1, CAP_PX, anchor="middle", name="foot-1")
    scene.text(W / 2, foot_y + 74, f2, CAP_PX, anchor="middle", name="foot-2")
    scene.text(W / 2, foot_y + 98, f3, CAP_PX, anchor="middle", name="foot-3")
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
