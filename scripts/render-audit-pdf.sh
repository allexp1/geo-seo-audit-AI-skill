#!/bin/bash
# Render an SEO audit HTML file to PDF via headless Chrome.
# Usage:
#   scripts/render-audit-pdf.sh input.html [output.pdf]
# If output.pdf is omitted, writes alongside the input with .pdf extension.

set -euo pipefail

INPUT="${1:-}"
OUTPUT="${2:-}"

if [[ -z "$INPUT" ]]; then
  echo "Usage: $0 input.html [output.pdf]" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Input file not found: $INPUT" >&2
  exit 1
fi

ABS_INPUT="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="${ABS_INPUT%.html}.pdf"
fi

# Try Chrome (macOS), Chromium (macOS), google-chrome / chromium (Linux).
CHROME=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)" \
  "$(command -v chromium-browser 2>/dev/null || true)"; do
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    CHROME="$candidate"
    break
  fi
done

if [[ -z "$CHROME" ]]; then
  echo "No Chrome/Chromium binary found. Install Chrome or set CHROME env var." >&2
  exit 1
fi

"$CHROME" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT" \
  "file://$ABS_INPUT" 2>&1 | grep -v "^$" >&2 || true

if [[ ! -s "$OUTPUT" ]]; then
  echo "PDF was not produced or is empty: $OUTPUT" >&2
  exit 1
fi

echo "PDF: $OUTPUT"
