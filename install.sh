#!/usr/bin/env bash
# ai-job-search-kr 설치 스크립트 (macOS · Linux)
#
#   bash install.sh          # 없는 것을 설치하고 포털 검색 도구를 준비한다
#   bash install.sh --check  # 설치하지 않고 상태만 보여준다
#
# 확인·설치하는 것: git, Python 3.10+, Bun, pandoc, Chrome, PDF 검사용 파이썬 패키지,
# 포털 검색 CLI 의존성, 그리고 Claude Code 또는 Codex CLI 중 하나.
set -u
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
OS="$(uname -s)"
OK=0; MISSING=0
ok()   { printf '  [OK]   %s\n' "$1"; OK=$((OK+1)); }
miss() { printf '  [없음] %s\n' "$1"; MISSING=$((MISSING+1)); }
info() { printf '  ...    %s\n' "$1"; }

have() { command -v "$1" >/dev/null 2>&1; }
brew_or_hint() {  # $1 패키지, $2 안내
  if [ "$CHECK_ONLY" = 1 ]; then miss "$1 ($2)"; return; fi
  if [ "$OS" = "Darwin" ] && have brew; then info "brew install $1"; brew install "$1" >/dev/null && ok "$1 설치" || miss "$1 설치 실패. $2"
  else miss "$1. $2"; fi
}

echo "== 1. 기본 도구"
have git && ok "git" || brew_or_hint git "https://git-scm.com 에서 설치"

PY=""
for c in python3 python; do
  if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -n "$PY" ]; then ok "Python $($PY -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
else brew_or_hint python "https://www.python.org/downloads 에서 3.10 이상 설치"; fi

if have bun; then ok "Bun $(bun --version)"
elif [ "$CHECK_ONLY" = 1 ]; then miss "Bun (https://bun.sh)"
else info "Bun 설치 (https://bun.sh)"; curl -fsSL https://bun.sh/install | bash >/dev/null 2>&1 && export PATH="$HOME/.bun/bin:$PATH" && have bun && ok "Bun 설치" || miss "Bun 설치 실패. https://bun.sh 참고"; fi

echo "== 2. PDF 생성"
have pandoc && ok "pandoc" || brew_or_hint pandoc "https://pandoc.org/installing.html"
CHROME="${CHROME_BIN:-}"
[ -z "$CHROME" ] && [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] && CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -z "$CHROME" ] && CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [ -n "$CHROME" ]; then ok "Chrome ($CHROME)"; else miss "Chrome. https://www.google.com/chrome 설치 후, 경로가 다르면 CHROME_BIN 환경변수로 지정"; fi

echo "== 3. 파이썬 패키지 (.venv)"
if [ -n "$PY" ]; then
  if [ "$CHECK_ONLY" = 1 ]; then
    [ -x .venv/bin/python ] && .venv/bin/python -c 'import pypdf' 2>/dev/null && ok ".venv + pypdf" || miss ".venv (bash install.sh 로 생성)"
  else
    [ -x .venv/bin/python ] || "$PY" -m venv .venv
    .venv/bin/python -m pip install -q --upgrade pip >/dev/null 2>&1 || true
    .venv/bin/python -m pip install -q pypdf pytest >/dev/null 2>&1 && ok ".venv + pypdf + pytest" || miss "pypdf 설치 실패. PDF 검사는 건너뛴다"
  fi
fi

echo "== 4. 포털 검색 도구"
for s in .agents/skills/*-search; do
  n="$(basename "$s")"
  if [ ! -f "$s/cli/package.json" ]; then continue; fi
  if [ "$CHECK_ONLY" = 1 ]; then
    [ -d "$s/cli/node_modules" ] && ok "$n" || miss "$n (bun install 필요)"
  elif have bun; then
    (cd "$s/cli" && bun install --silent >/dev/null 2>&1) && ok "$n" || miss "$n bun install 실패"
  else miss "$n (Bun 없음)"; fi
done

echo "== 4.5 프로필 파일"
for t in .agents/skills/job-application-assistant/01-candidate-profile .agents/skills/job-application-assistant/03-glossary .agents/skills/job-application-assistant/05-profiles .agents/skills/job-scraper/search-config; do
  if [ -f "$t.md" ]; then ok "$(basename $t).md (있음)"
  elif [ "$CHECK_ONLY" = 1 ]; then miss "$(basename $t).md (bash install.sh 가 템플릿에서 만든다)"
  else cp "$t.template.md" "$t.md" && ok "$(basename $t).md 템플릿에서 생성"; fi
done

echo "== 5. 에이전트"
have claude && ok "Claude Code ($(claude --version 2>/dev/null | head -1))" || miss "Claude Code. https://claude.com/claude-code (둘 중 하나면 된다)"
have codex && ok "Codex CLI ($(codex --version 2>/dev/null | head -1))" || miss "Codex CLI. https://developers.openai.com/codex (둘 중 하나면 된다)"

echo "== 6. 동작 확인"
if have bun && [ -d .agents/skills/wanted-search/cli/node_modules ]; then
  if bun run .agents/skills/wanted-search/cli/src/cli.ts search -q "백엔드 개발자" --limit 1 --format json >/dev/null 2>&1; then ok "원티드 검색 응답"; else miss "원티드 검색 실패. 네트워크를 확인한다"; fi
fi

echo
echo "정상 $OK, 없음 $MISSING"
if [ "$MISSING" -gt 0 ]; then
  echo "위 [없음] 항목을 해결한 뒤 다시 실행한다. Claude Code와 Codex는 하나만 있으면 된다."
else
  echo "준비 끝. 다음 순서:"
  echo "  1) documents/resume/ 에 이력서 파일을 넣는다 (있으면 포트폴리오는 documents/portfolio/)"
  echo "  2) claude 또는 codex 를 이 폴더에서 연다"
  echo "  3) /setup (Codex는 \$setup) 을 입력한다"
fi
