#!/usr/bin/env bash
# tools/build_pdf.py 로 넘기는 래퍼. 윈도우에서는 build_pdf.py 를 직접 부른다.
#   bash tools/build_pdf.sh <in.md> <out.pdf> [resume|doc]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python)"
exec "$PY" "$HERE/build_pdf.py" "$@"
