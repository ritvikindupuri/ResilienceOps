#!/usr/bin/env bash
# Render docs/architecture.svg (canonical source) to
# docs/images/infraattack_platform_architecture.png
#
# Preferred: rsvg-convert (librsvg). Fallback: headless Chrome/Chromium.
# Companion mermaid source is docs/architecture.mmd (not used for the PNG;
# mermaid LR/TB layouts were too cramped for this architecture).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/docs/architecture.svg"
OUT="$ROOT/docs/images/infraattack_platform_architecture.png"

if [[ ! -f "$SVG" ]]; then
  echo "missing $SVG" >&2
  exit 1
fi

if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 2000 -h 1080 "$SVG" -o "$OUT"
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
  --window-size=2000,1080 \
  --virtual-time-budget=4000 \
  --screenshot="$OUT" \
  "file://$SVG" >/tmp/architecture-chrome.log 2>&1 || true
if [[ ! -s "$OUT" ]]; then
  echo "screenshot failed; see /tmp/architecture-chrome.log" >&2
  exit 1
fi
echo "wrote $OUT via Chrome ($(wc -c < "$OUT") bytes)"
