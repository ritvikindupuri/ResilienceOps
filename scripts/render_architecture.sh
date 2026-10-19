#!/usr/bin/env bash
# Rebuild docs/architecture.svg from scripts/build_architecture.py + docs/icons/,
# then rasterize to docs/images/infraattack_platform_architecture.png.
#
# Preferred rasterizer: rsvg-convert (librsvg). Fallback: headless Chrome.
# Companion mermaid source: docs/architecture.mmd (same flow, no icons).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/docs/architecture.svg"
OUT="$ROOT/docs/images/infraattack_platform_architecture.png"

python3 "$ROOT/scripts/build_architecture.py"

if [[ ! -f "$SVG" ]]; then
  echo "missing $SVG" >&2
  exit 1
fi

if command -v rsvg-convert >/dev/null 2>&1; then
  # 2× the native viewBox so README width=950 stays sharp.
  rsvg-convert --zoom=2 "$SVG" -o "$OUT"
  echo "wrote $OUT via rsvg-convert ($(wc -c < "$OUT") bytes)"
  exit 0
fi

CHROME="${CHROME:-/usr/local/bin/google-chrome}"
if [[ ! -x "$CHROME" ]]; then
  CHROME="$(command -v google-chrome || command -v chromium || true)"
fi
if [[ -z "${CHROME}" ]]; then
  echo "rsvg-convert and google-chrome/chromium not found" >&2
  echo "install librsvg2-bin (Debian/Ubuntu) or Google Chrome, then re-run." >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
cleanup() { rm -rf "$tmpdir"; pkill -f "user-data-dir=$tmpdir" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Chrome headless often stays alive after --screenshot; bound it with timeout(1).
timeout 20s "$CHROME" \
  --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --user-data-dir="$tmpdir" \
  --default-background-color=FFFFFFFF \
  --window-size=4200,2840 \
  --virtual-time-budget=4000 \
  --screenshot="$OUT" \
  "file://$SVG" >/tmp/architecture-chrome.log 2>&1 || true
if [[ ! -s "$OUT" ]]; then
  echo "screenshot failed; see /tmp/architecture-chrome.log" >&2
  exit 1
fi
echo "wrote $OUT via Chrome ($(wc -c < "$OUT") bytes)"
