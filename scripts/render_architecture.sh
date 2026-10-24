#!/usr/bin/env bash
# Rebuild architecture SVGs from scripts/build_architecture.py + docs/icons/,
# then rasterize the main figure and the agent-sandbox figure.
#
# Preferred rasterizer: rsvg-convert (librsvg). Fallback: headless Chrome.
# Companion mermaid source: docs/architecture.mmd (same flow, no icons).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$ROOT/scripts/build_architecture.py"

rasterize() {
  local svg="$1"
  local out="$2"
  local width="$3"
  local height="$4"
  if [[ ! -f "$svg" ]]; then
    echo "missing $svg" >&2
    return 1
  fi
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert --zoom=2 "$svg" -o "$out"
    echo "wrote $out via rsvg-convert ($(wc -c < "$out") bytes)"
    return 0
  fi
  local chrome="${CHROME:-/usr/local/bin/google-chrome}"
  if [[ ! -x "$chrome" ]]; then
    chrome="$(command -v google-chrome || command -v chromium || true)"
  fi
  if [[ -z "${chrome}" ]]; then
    echo "rsvg-convert and google-chrome/chromium not found" >&2
    echo "install librsvg2-bin (Debian/Ubuntu) or Google Chrome, then re-run." >&2
    return 1
  fi
  local tmpdir
  tmpdir="$(mktemp -d)"
  cleanup() { rm -rf "$tmpdir"; pkill -f "user-data-dir=$tmpdir" >/dev/null 2>&1 || true; }
  trap cleanup EXIT
  timeout 20s "$chrome" \
    --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir="$tmpdir" \
    --default-background-color=FFFFFFFF \
    --window-size="$width,$height" \
    --virtual-time-budget=4000 \
    --screenshot="$out" \
    "file://$svg" >/tmp/architecture-chrome.log 2>&1 || true
  trap - EXIT
  cleanup
  if [[ ! -s "$out" ]]; then
    echo "screenshot failed; see /tmp/architecture-chrome.log" >&2
    return 1
  fi
  echo "wrote $out via Chrome ($(wc -c < "$out") bytes)"
}

rasterize \
  "$ROOT/docs/architecture.svg" \
  "$ROOT/docs/images/infraattack_platform_architecture.png" \
  2960 2560
rasterize \
  "$ROOT/docs/sandbox_architecture.svg" \
  "$ROOT/docs/images/agent_sandbox_architecture.png" \
  2360 1560
