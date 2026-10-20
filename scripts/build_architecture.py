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
    elif thin:
        cls = "arrow-thin"
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
HEAD_GAP = 6.0
ICON_HALO = 10.0
END_SLOP = 8.0


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


def _text_belongs(text_name: str, touch: frozenset[str]) -> bool:
    if not touch:
        return False
    if text_name in touch:
        return True
    for item in touch:
        if text_name.startswith(item) or item.startswith(text_name):
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
        self.edges: list[tuple[str, tuple[float, float], tuple[float, float], str, str, str]] = []
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
        rel: str = "",
    ) -> None:
        if abs(x1 - x2) < 0.5 and abs(y1 - y2) < 0.5:
            return
        self.segments.append((x1, y1, x2, y2, name, touch, rel or _polyline_id(name)))

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
        touch: tuple[str, ...] = (),
        rel: str = "",
        src: str = "",
        dst: str = "",
    ) -> None:
        self.add(poly(points, dashed=dashed, marked=marked, inc=inc, thin=thin))
        self._mark(name, marked)
        owned = frozenset(touch)
        family = rel or name
        self.edges.append((name, points[0], points[-1], src, dst, family))
        for i in range(len(points) - 1):
            self.add_seg(*points[i], *points[i + 1], f"{name}:{i}", owned, rel=family)

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
        touch: tuple[str, ...] = (),
        rel: str = "",
        src: str = "",
        dst: str = "",
    ) -> None:
        self.add(arrow(x1, y1, x2, y2, dashed=dashed, inc=inc, thin=thin))
        self._mark(name, True)
        family = rel or name
        owned = frozenset(touch)
        self.edges.append((name, (x1, y1), (x2, y2), src, dst, family))
        self.add_seg(x1, y1, x2, y2, name, owned, rel=family)

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
        # Crossings: skip a T-junction (shared endpoint) unless two *different*
        # relationships overlap on a collinear run — that is a merged corridor.
        for i, s1 in enumerate(self.segments):
            rel1 = s1[6] if len(s1) > 6 else _polyline_id(s1[4])
            h1 = abs(s1[1] - s1[3]) < 0.6
            for s2 in self.segments[i + 1 :]:
                rel2 = s2[6] if len(s2) > 6 else _polyline_id(s2[4])
                h2 = abs(s2[1] - s2[3]) < 0.6
                collinear = _collinear_overlap(s1, s2, h1) if h1 and h2 else (
                    _collinear_overlap(s1, s2, False) if (not h1 and not h2) else False
                )
                if collinear and rel1 != rel2:
                    hits.append(
                        f"shared collinear {rel1} × {rel2} "
                        f"({s1[4]} {s1[0]:.0f},{s1[1]:.0f}-{s1[2]:.0f},{s1[3]:.0f} / "
                        f"{s2[4]} {s2[0]:.0f},{s2[1]:.0f}-{s2[2]:.0f},{s2[3]:.0f})"
                    )
                    continue
                if _share_endpoint(s1, s2):
                    continue
                if _proper_intersect(s1, s2):
                    hits.append(
                        f"polylines {_polyline_id(s1[4])} × {_polyline_id(s2[4])} "
                        f"({s1[4]} {s1[0]:.0f},{s1[1]:.0f}-{s1[2]:.0f},{s1[3]:.0f} / "
                        f"{s2[4]} {s2[0]:.0f},{s2[1]:.0f}-{s2[2]:.0f},{s2[3]:.0f})"
                    )
        # Text: 10px halo unless the segment belongs to that label.
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
                    hits.append(f"line {s[4]} near text {b[4]} (<{TEXT_CLEARANCE:.0f}px)")
        # Boxes: a segment may only clip a box it starts or ends in.
        # Background frames (host/compose/deploy/external/k3s) are not obstacles;
        # node-like groups (Agents, Target services) may only be touched at the border.
        background = {
            "group:laptop",
            "group:aws",
            "group:host",
            "group:compose",
            "group:bot",
            "group:k3s",
        }
        solid_groups = {"group:agents", "group:services"}
        for s in self.segments:
            touch = s[5] if len(s) > 5 else frozenset()
            for b in self.boxes:
                if b[5] in {"icon", "badge"}:
                    connected = _text_belongs(b[4], touch) or _endpoint_in_box(s, b, slop=END_SLOP)
                    if b[5] == "icon" and not connected:
                        inf = (
                            b[0] - ICON_HALO,
                            b[1] - ICON_HALO,
                            b[2] + 2 * ICON_HALO,
                            b[3] + 2 * ICON_HALO,
                        )
                        if _seg_clip_len(s, inf) > 0.5:
                            hits.append(f"line {s[4]} near icon {b[4]} (<{ICON_HALO:.0f}px)")
                            continue
                    if connected:
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
        icons = {b[4]: b for b in self.boxes if b[5] == "icon"}
        for name, start, end, src, dst, _rel in self.edges:
            for pt, label, kind in ((start, src, "start"), (end, dst, "end")):
                if not label:
                    continue
                box = icons.get(label)
                if box is None:
                    hits.append(f"endpoint {name} {kind} unknown icon {label}")
                    continue
                if not _pt_in_box(pt[0], pt[1], box, END_SLOP):
                    hits.append(
                        f"endpoint {name} {kind} {pt[0]:.0f},{pt[1]:.0f} "
                        f"not within {END_SLOP:.0f}px of {label}"
                    )
        return hits


def build() -> str:
    svg, _violations = build_scene()
    return svg


def build_scene() -> tuple[str, list[str]]:
    W, H = 1600, 1224
    scene = Scene(W, H)

    # Deploy band. Elbows leave each source top, run a private lane, and
    # drop onto the matching target top. Lanes are 120 / 132 / 144.
    dep_y, dep_h = 76, 196
    lap_x, lap_w = 24, 760
    aws_x, aws_w = 800, 776
    sat_y = 196
    sat_size = 30
    sat_top = sat_y - sat_size / 2
    # Laptop L→R: Terraform, Deploy, Secrets. AWS L→R: Param, S3, SSM so
    # Secrets→Param never crosses Deploy's up-shaft.
    tf_x, dep_x, sec_x = 160, 360, 590
    par_x, s3_x, ssm_x = 920, 1150, 1440
    drop_x = 1048
    lane_ssm, lane_s3, lane_par = 120, 132, 144

    host_x, host_y, host_w, host_h = 24, 280, 1204, 820
    bot_x, bot_y, bot_w, bot_h = 1240, 280, 336, 820

    compose_x, compose_y = 36, 364
    compose_w, compose_h = 1188, 650
    k3s_x, k3s_y, k3s_w, k3s_h = 36, 1024, 1188, 70

    agents_x, agents_y, agents_w, agents_h = 48, 420, 272, 480
    red_x, red_y = 182, 555
    blue_x, blue_y = 182, 780

    # OS left (owns the DB drop), payment to its right, api-gw on the
    # right so Traffic can enter from outside the group.
    svc_x, svc_y, svc_w, svc_h = 400, 420, 400, 450
    os_x, gw_x, ps_x = 560, 745, 480
    os_y, gw_y, ps_y = 716, 720, 600

    row_a = _ic(red_y)
    prom_x, am_x, br_x = 870, 1020, 1135
    prom_y = am_y = br_y = red_y
    graf_x, graf_y = 960, 740

    rd_x, pg_x, tg_x, db_y = 500, 640, 810, 920
    os_db_y = 860
    bq_y = 1012
    scrape_up = 820
    blue_gw_up = 700
    scrape_floor = 995
    scrape_hop = 430
    query_up = 890
    blue_floor = 1006
    query_left_y = 720
    scrape_drop = 720

    grok_x, grok_y = 1380, 555
    gh_x, ping_x, gh_y, ping_y = 1500, 1500, 700, 880

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
      .arrow-thin {{ stroke: #9CA3AF; stroke-width: 1.35; fill: none; }}
      .arrow-inc {{ stroke: {INC_ORANGE}; stroke-width: 3.4; fill: none; }}
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

    scene.add(group(lap_x, dep_y, lap_w, dep_h, "Deploy (optional AWS) · laptop", style="account"))
    scene.container("laptop", lap_x, dep_y, lap_w, dep_h)
    scene.text(lap_x + 18, dep_y + 28, "Deploy (optional AWS) · laptop", GROUP_PX, bold=True, name="group:laptop", container="laptop")
    scene.add(group(aws_x, dep_y, aws_w, dep_h, "AWS", icon="aws-logo", style="account"))
    scene.container("aws", aws_x, dep_y, aws_w, dep_h)
    scene.text(aws_x + 40, dep_y + 28, "AWS", GROUP_PX, bold=True, name="group:aws", container="aws")

    scene.satellite_at(tf_x, sat_y, "terraform", "Terraform", "creates the infra", container="laptop")
    scene.satellite_at(dep_x, sat_y, "document", "Deploy script", "", name_size=22, container="laptop")
    scene.satellite_at(sec_x, sat_y, "document", "Secrets script", "", name_size=22, container="laptop")
    scene.satellite_at(par_x, sat_y, "aws-param-store", "Parameter Store", "holds secrets", name_size=22, container="aws")
    scene.satellite_at(s3_x, sat_y, "aws-s3", "S3", "stores the app bundle", container="aws")
    scene.satellite_at(ssm_x, sat_y, "aws-ssm", "SSM", "runs deploy commands", container="aws")

    host_title = "EC2 host · public subnet 10.0.1.0/24 · VPC 10.0.0.0/16"
    host_sg = "SG :3000/:8000 from allowed_cidr"
    scene.add(group(host_x, host_y, host_w, host_h, host_title, icon="aws-ec2", style="host"))
    scene.container("host", host_x, host_y, host_w, host_h)
    scene.text(host_x + 40, host_y + 28, host_title, GROUP_PX, bold=True, name="host-title", container="host")
    scene.add(f'  <text x="{host_x + 40:.0f}" y="{host_y + 50:.0f}" class="cap">{host_sg}</text>')
    scene.text(host_x + 40, host_y + 50, host_sg, CAP_PX, name="host-sg", container="host")
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

    scene.add(group(svc_x, svc_y, svc_w, svc_h, "Target services", style=None))
    scene.container("services", svc_x, svc_y, svc_w, svc_h)
    scene.text(svc_x + 14, svc_y + 26, "Target services", GROUP_PX, bold=True, name="group:services", container="services")

    k3s_title = "k3s sandbox (optional)"
    k3s_sub = "agents in one sandbox pod"
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
    scene.add(
        f'  <text x="{blue_x:.0f}" y="{blue_y + 100:.0f}" text-anchor="middle" class="cap">queries Prometheus</text>'
    )
    scene.text(
        blue_x, blue_y + 100, "queries Prometheus", CAP_PX, anchor="middle",
        name="cap3:Blue Team", container="agents",
    )
    scene.node_at(gw_x, gw_y, "fastapi", "api-gw", "", container="services")
    scene.node_at(os_x, os_y, "fastapi", "order-", "", name2="service", container="services")
    scene.node_at(ps_x, ps_y, "fastapi", "payment-", "", name2="service", container="services")
    scene.node_at(prom_x, prom_y, "prometheus", "Prometheus", "pulls /metrics", container="compose")
    scene.node_at(am_x, am_y, "alertmanager", "Alert", "", name2="manager", container="compose")
    scene.node_at(br_x, br_y, "document", "incident-", "adds evidence", name2="bridge", container="compose", name_size=22)
    scene.node_at(tg_x, db_y, "traffic", "Traffic", "load", container="compose")
    scene.node_at(rd_x, db_y, "redis", "Redis", "cache", container="compose")
    scene.node_at(pg_x, db_y, "postgresql", "PostgreSQL", "orders_db", container="compose")
    scene.node_at(graf_x, graf_y, "grafana", "Grafana", "reads Prom", size=48, container="compose")
    scene.grok_at(grok_x, grok_y, "AI Incident Diagnosis", container="bot")
    scene.node_at(gh_x, gh_y, "github", "GitHub", "incident", name2="issue", name_size=22, container="bot")
    scene.node_at(ping_x, ping_y, "bell", "Owner ping", "critical", name_size=22, container="bot")

    gw_ic = _ic(gw_y)
    os_ic = _ic(os_y)
    ps_ic = _ic(ps_y)
    blue_ic = _ic(blue_y)
    gw_tick_y = gw_ic + 14
    os_tick_y = os_ic + 22
    ps_tick_y = ps_ic + 14
    red_right = red_x + ICON / 2 + HEAD_GAP
    blue_right = blue_x + ICON / 2 + HEAD_GAP
    blue_icon_left = blue_x - ICON / 2
    blue_icon_bot = _icon_top(blue_y) + ICON
    gw_left = gw_x - ICON / 2 - HEAD_GAP
    gw_right = gw_x + ICON / 2 + HEAD_GAP
    os_left = os_x - ICON / 2 - HEAD_GAP
    os_right = os_x + ICON / 2 + HEAD_GAP
    os_top = _icon_top(os_y)
    os_bot = os_top + ICON + HEAD_GAP
    ps_left = ps_x - ICON / 2 - HEAD_GAP
    ps_top = _icon_top(ps_y)
    prom_left = prom_x - ICON / 2 - HEAD_GAP
    prom_right = prom_x + ICON / 2 + HEAD_GAP
    prom_top = _icon_top(prom_y)
    prom_bot = prom_top + ICON + HEAD_GAP
    am_left = am_x - ICON / 2 - HEAD_GAP
    am_right = am_x + ICON / 2 + HEAD_GAP
    br_left = br_x - ICON / 2 - HEAD_GAP
    br_right = br_x + ICON / 2 + HEAD_GAP
    br_top = _icon_top(br_y)
    grok_left, grok_right = grok_x - 48, grok_x + 48
    gh_left = gh_x - ICON / 2 - HEAD_GAP
    ping_left = ping_x - ICON / 2 - HEAD_GAP
    ping_ic = _ic(ping_y)
    gh_ic = _ic(gh_y)
    graf_top = _icon_top(graf_y, 48)
    db_top = _icon_top(db_y)
    fork_x = 400
    fork_bot = 1455
    blue_bus = 420
    blue_exit = 88
    query_rail = 68
    badge_y = row_a - 28
    promql_y = 400
    blue_caps = ("cap:Blue Team", "cap2:Blue Team", "cap3:Blue Team", "icon:Blue Team", "name:Blue Team")

    # Deploy elbows: up from each source top, across a private lane, down onto
    # the target top. Lanes are 120 / 132 / 144 as specified.
    scene.poly(
        [
            (sec_x, sat_top - HEAD_GAP),
            (sec_x, lane_par),
            (par_x, lane_par),
            (par_x, sat_top - HEAD_GAP),
        ],
        name="sec-param",
        src="sat-icon:Secrets script",
        dst="sat-icon:Parameter Store",
        touch=("sat-icon:Secrets script", "sat-icon:Parameter Store", "sat:Secrets script", "sat:Parameter Store", "sat-cap:Parameter Store"),
    )
    scene.poly(
        [
            (dep_x, sat_top - HEAD_GAP),
            (dep_x, lane_s3),
            (s3_x, lane_s3),
            (s3_x, sat_top - HEAD_GAP),
        ],
        name="dep-s3",
        rel="deploy-out",
        src="sat-icon:Deploy script",
        dst="sat-icon:S3",
        touch=("sat-icon:Deploy script", "sat-icon:S3", "sat:Deploy script", "sat:S3", "sat-cap:S3"),
    )
    scene.poly(
        [
            (dep_x, sat_top - HEAD_GAP),
            (dep_x, lane_s3),
            (dep_x, lane_ssm),
            (ssm_x, lane_ssm),
            (ssm_x, sat_top - HEAD_GAP),
        ],
        name="dep-ssm",
        rel="deploy-out",
        src="sat-icon:Deploy script",
        dst="sat-icon:SSM",
        touch=("sat-icon:Deploy script", "sat-icon:SSM", "sat:Deploy script", "sat:SSM", "sat-cap:SSM"),
    )
    scene.arrow(drop_x, dep_y + dep_h, drop_x, host_y, name="aws-host")

    # ① from the Red icon, fork just inside the services padding (right of
    # Blue's bus) so the orange landings never share Blue's vertical.
    scene.poly(
        [
            (red_right, row_a),
            (fork_x, row_a),
            (fork_x, scrape_hop),
            (os_x, scrape_hop),
            (os_x, os_top - HEAD_GAP),
        ],
        inc=True,
        name="fault-os",
        rel="fault",
        src="icon:Red Team",
        dst="icon:order-",
        touch=("icon:Red Team", "icon:order-", "name:Red Team", "name:order-", "name2:order-", "badge:1", "name:payment-", "name2:payment-", "icon:payment-", "group:services"),
    )
    scene.poly(
        [
            (red_right, row_a),
            (fork_x, row_a),
            (fork_x, scrape_hop),
            (ps_x, scrape_hop),
            (ps_x, ps_top - HEAD_GAP),
        ],
        inc=True,
        name="fault-ps",
        rel="fault",
        src="icon:Red Team",
        dst="icon:payment-",
        touch=("icon:Red Team", "icon:payment-", "name:Red Team", "name:payment-", "name2:payment-", "badge:1", "group:services", "name:api-gw", "icon:api-gw"),
    )
    scene.badge(fork_x - 70, badge_y, 1, container="compose")

    # ② drops under the stores, climbs east of Traffic, then into Prometheus.
    scene.poly(
        [
            (os_right, os_ic),
            (scrape_drop, os_ic),
            (scrape_drop, scrape_floor),
            (scrape_up, scrape_floor),
            (scrape_up, scrape_hop),
            (prom_left, scrape_hop),
            (prom_left, row_a),
        ],
        inc=True,
        name="scrape",
        src="icon:order-",
        dst="icon:Prometheus",
        touch=("icon:order-", "icon:Prometheus", "name:order-", "name2:order-", "name:Prometheus", "cap:Prometheus", "name:Traffic", "cap:Traffic", "icon:Traffic", "name:PostgreSQL", "cap:PostgreSQL", "badge:2", "name:api-gw"),
    )
    scene.badge(prom_left - 36, badge_y, 2, container="compose")
    scene.arrow(
        prom_right, row_a, am_left, row_a, inc=True, name="prom-am",
        src="icon:Prometheus", dst="icon:Alert",
        touch=("icon:Prometheus", "icon:Alert"),
    )
    scene.badge((prom_x + am_x) / 2, badge_y, 3, container="compose")
    scene.arrow(
        am_right, row_a, br_left, row_a, inc=True, name="am-br",
        src="icon:Alert", dst="icon:incident-",
        touch=("icon:Alert", "icon:incident-"),
    )
    scene.badge((am_x + br_x) / 2, badge_y, 4, container="compose")
    scene.arrow(
        br_right, row_a, grok_left, row_a, inc=True, name="br-bot",
        src="icon:incident-", dst="icon:grok",
        touch=("icon:incident-", "icon:grok"),
    )
    scene.badge(bot_x + 22, badge_y, 5, container="bot")
    scene.poly(
        [(grok_right, row_a), (fork_bot, row_a), (fork_bot, gh_ic), (gh_left, gh_ic)],
        inc=True,
        name="bot-gh",
        rel="bot-out",
        src="icon:grok",
        dst="icon:GitHub",
        touch=("icon:grok", "icon:GitHub", "name:grok1", "name:grok2"),
    )
    scene.poly(
        [(grok_right, row_a), (fork_bot, row_a), (fork_bot, ping_ic), (ping_left, ping_ic)],
        inc=True,
        name="bot-ping",
        rel="bot-out",
        src="icon:grok",
        dst="icon:Owner ping",
        touch=("icon:grok", "icon:Owner ping", "name:grok1", "name:grok2", "name:GitHub", "cap:GitHub", "name2:GitHub"),
    )
    scene.badge(fork_bot, badge_y, 6, container="bot")

    scene.poly(
        [
            (br_x, br_top - HEAD_GAP),
            (br_x, promql_y),
            (prom_x, promql_y),
            (prom_x, prom_top - HEAD_GAP),
        ],
        dashed=True,
        name="promql",
        src="icon:incident-",
        dst="icon:Prometheus",
        touch=("icon:incident-", "icon:Prometheus", "name:Prometheus", "cap:Prometheus", "name:incident-", "name2:incident-"),
    )

    prom_icon_right = prom_x + ICON / 2
    prom_icon_bot = prom_top + ICON
    scene.poly(
        [
            (prom_icon_right - 4, prom_icon_bot - 4),
            (graf_x, prom_icon_bot - 4),
            (graf_x, graf_top - HEAD_GAP),
        ],
        name="prom-graf",
        src="icon:Prometheus",
        dst="icon:Grafana",
        touch=("icon:Prometheus", "icon:Grafana", "cap:Prometheus", "cap:Grafana", "name:Grafana", "name:Prometheus", "name2:Alert", "name:Alert"),
    )

    # order-service → DBs: own drop and own horizontal. Nothing else joins it.
    scene.poly(
        [(os_x, os_bot), (os_x, os_db_y), (rd_x, os_db_y), (rd_x, db_top - HEAD_GAP)],
        name="os-redis",
        rel="os-db",
        src="icon:order-",
        dst="icon:Redis",
        touch=("icon:order-", "icon:Redis", "name:order-", "name2:order-", "name:Redis", "cap:Redis"),
    )
    scene.poly(
        [(os_x, os_bot), (os_x, os_db_y), (pg_x, os_db_y), (pg_x, db_top - HEAD_GAP)],
        name="os-pg",
        rel="os-db",
        src="icon:order-",
        dst="icon:PostgreSQL",
        touch=("icon:order-", "icon:PostgreSQL", "name:order-", "name2:order-", "name:PostgreSQL", "cap:PostgreSQL"),
    )

    # Traffic → api-gw: own vertical outside the services group, into the right.
    scene.poly(
        [(tg_x, db_top - HEAD_GAP), (tg_x, gw_ic), (gw_right, gw_ic)],
        name="traffic-gw",
        src="icon:Traffic",
        dst="icon:api-gw",
        touch=("icon:Traffic", "icon:api-gw", "name:Traffic", "cap:Traffic", "name:api-gw", "name:Prometheus", "cap:Prometheus", "badge:2"),
    )

    # Blue health: gutter bus for OS; gw and payment walk the lab floor so
    # they never share ① or the OS→DB drop.
    scene.poly(
        [
            (blue_icon_left, blue_ic),
            (blue_exit, blue_ic),
            (blue_exit, blue_floor),
            (blue_bus, blue_floor),
            (blue_bus, os_tick_y),
            (os_left, os_tick_y),
        ],
        thin=True,
        name="blue-os",
        rel="blue-health",
        src="icon:Blue Team",
        dst="icon:order-",
        touch=blue_caps + ("icon:order-", "name:order-", "name2:order-"),
    )
    scene.poly(
        [
            (blue_icon_left, blue_ic),
            (blue_exit, blue_ic),
            (blue_exit, blue_floor),
            (blue_bus, blue_floor),
            (blue_bus, ps_tick_y),
            (ps_left, ps_tick_y),
        ],
        thin=True,
        name="blue-ps",
        rel="blue-health",
        src="icon:Blue Team",
        dst="icon:payment-",
        touch=blue_caps + ("icon:payment-", "name:payment-", "name2:payment-"),
    )
    scene.poly(
        [
            (blue_icon_left, blue_ic),
            (blue_exit, blue_ic),
            (blue_exit, blue_floor),
            (blue_gw_up, blue_floor),
            (blue_gw_up, gw_tick_y),
            (gw_left, gw_tick_y),
        ],
        thin=True,
        name="blue-gw",
        rel="blue-health",
        src="icon:Blue Team",
        dst="icon:api-gw",
        touch=blue_caps + ("icon:api-gw", "name:api-gw", "name:payment-", "name2:payment-", "name:PostgreSQL", "cap:PostgreSQL"),
    )

    # Blue query: starts at the Blue icon, along the Lab floor, up to Prometheus' lower edge.
    scene.poly(
        [
            (blue_icon_left, query_left_y),
            (query_rail, query_left_y),
            (query_rail, bq_y),
            (query_up, bq_y),
            (query_up, prom_bot),
            (prom_left, prom_bot),
        ],
        dashed=True,
        name="blue-promql",
        src="icon:Blue Team",
        dst="icon:Prometheus",
        touch=blue_caps + ("icon:Prometheus", "name:Prometheus", "cap:Prometheus", "name:Traffic", "cap:Traffic", "icon:Traffic"),
    )

    host_bottom = host_y + host_h
    leg_y = host_bottom + 28
    leg_y2 = leg_y + 26
    scene.add(
        f'  <line x1="36" y1="{leg_y}" x2="70" y2="{leg_y}" class="arrow-inc"/>'
        f'  <text x="80" y="{leg_y + 6}" class="legend">1–6 incident path</text>'
        f'  <line x1="300" y1="{leg_y}" x2="334" y2="{leg_y}" class="arrow"/>'
        f'  <text x="344" y="{leg_y + 6}" class="legend">supporting</text>'
        f'  <line x1="36" y1="{leg_y2}" x2="80" y2="{leg_y2}" class="arrow"/>'
        f'  <line x1="88" y1="{leg_y2}" x2="132" y2="{leg_y2}" class="arrow" stroke-dasharray="7 6"/>'
        f'  <text x="144" y="{leg_y2 + 6}" class="legend">'
        f"solid = data flow · dashed = query (arrow points to what's queried)</text>"
    )
    scene.text(80, leg_y + 6, "1–6 incident path", CAP_PX, name="legend-inc")
    scene.text(344, leg_y + 6, "supporting", CAP_PX, name="legend-sup")
    scene.text(
        144,
        leg_y2 + 6,
        "solid = data flow · dashed = query (arrow points to what's queried)",
        CAP_PX,
        name="legend-q",
    )
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
