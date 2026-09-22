#!/usr/bin/env bash
# 휴머나이저 스킬을 업스트림(epoko77-ai/im-not-ai)에서 다시 복사한다.
#   bash tools/update_humanizer.sh            # GitHub에서 임시 클론
#   bash tools/update_humanizer.sh <로컬 클론 경로>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/.agents/skills/humanize-korean"
SRC="${1:-}"
TMP=""
if [ -z "$SRC" ]; then
  TMP="$(mktemp -d)"; git clone -q --depth 1 https://github.com/epoko77-ai/im-not-ai.git "$TMP/im-not-ai"; SRC="$TMP/im-not-ai"
fi
[ -d "$SRC/codex/skills/humanize-korean" ] || { echo "업스트림에 codex/skills/humanize-korean 이 없다: $SRC" >&2; exit 1; }
HASH="$(git -C "$SRC" rev-parse HEAD)"; DATE="$(git -C "$SRC" log -1 --format=%ad --date=short)"
VER="$(grep -m1 '"version"' "$SRC/.claude-plugin/plugin.json" | grep -oE '[0-9.]+' || echo "?")"
# SKILL.md 가 참조하는 파일만 가져온다. 메트릭 스크립트·baseline·웹 명세는 strict 모드용이라 제외
find "$DEST" -mindepth 1 ! -name UPSTREAM.md -exec rm -rf {} + 2>/dev/null || true
mkdir -p "$DEST/references"
cp -L "$SRC/codex/skills/humanize-korean/SKILL.md" "$DEST/SKILL.md"
for f in quick-rules.md rewriting-playbook.md ai-tell-taxonomy.md scholarship.md; do cp -L "$SRC/codex/skills/humanize-korean/references/$f" "$DEST/references/$f"; done
python3 - "$DEST/UPSTREAM.md" "$HASH" "$DATE" "$VER" "$(date +%Y-%m-%d)" <<'PY'
import re,sys
p,h,d,v,today=sys.argv[1:]
s=open(p,encoding='utf-8').read()
s=re.sub(r'\| 업스트림 커밋 \| `[^`]*` \|', f'| 업스트림 커밋 | `{h}` |', s)
s=re.sub(r'\| 업스트림 날짜 \| [^|]* \|', f'| 업스트림 날짜 | {d} |', s)
s=re.sub(r'\| 플러그인 버전 \| [^|]* \|', f'| 플러그인 버전 | {v} |', s)
s=re.sub(r'\| 복사한 날 \| [^|]* \|', f'| 복사한 날 | {today} |', s)
open(p,'w',encoding='utf-8').write(s)
PY
[ -n "$TMP" ] && rm -rf "$TMP"
echo "휴머나이저 갱신: $HASH ($DATE, v$VER)"
