#!/usr/bin/env bash
# 마크다운 → PDF. pandoc + Chrome 헤드리스.
# 사용: bash tools/build_pdf.sh <in.md> <out.pdf> [resume|doc]
set -euo pipefail
IN="${1:?입력 md 경로}"
OUT="${2:?출력 pdf 경로}"
MODE="${3:-doc}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
case "$MODE" in
  resume) CSS="$ROOT/templates/assets/resume.css" ;;
  doc)    CSS="$ROOT/templates/assets/doc.css" ;;
  *) echo "모드는 resume 또는 doc" >&2; exit 2 ;;
esac
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ -x "$CHROME" ] || CHROME="$(command -v google-chrome || command -v chromium || true)"
[ -n "$CHROME" ] && [ -x "$CHROME" ] || { echo "Chrome을 찾지 못했다. CHROME_BIN을 설정한다" >&2; exit 2; }
command -v pandoc >/dev/null || { echo "pandoc이 없다" >&2; exit 2; }

TMP="$(mktemp -t ajskr).html"
# --metadata title="" : 제목 블록이 H1과 중복되는 것을 막는다
# hard_line_breaks   : **기간** / **역할** 줄이 합쳐지는 것을 막는다
pandoc "$IN" -f gfm+hard_line_breaks -t html5 -s --metadata title="" \
  -c "$CSS" --embed-resources -o "$TMP"
OUT_ABS="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT_ABS" "file://$TMP" 2>/dev/null
rm -f "$TMP"
echo "$OUT_ABS"
