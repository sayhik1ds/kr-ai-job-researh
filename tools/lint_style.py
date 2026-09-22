#!/usr/bin/env python3
"""한국어 문체 규칙과 사내 용어를 검사한다.

검사 대상은 이 저장소가 한국어로 쓴 문서다. 지원 문서, 워크플로 스킬, README, 방법론 파일.
대상이 아닌 것: 영어로 쓴 포털 검색 스킬(`*-search/SKILL.md`), 복사본인 `humanize-korean/`.
영어 산문은 em-dash를 정상으로 쓰고, 복사본은 고치지 않는다.
규칙 파일 자체(`02-writing-style.md`, `03-glossary*.md`)도 건너뛴다. 금지 패턴을 데이터로 담고 있어
검사하면 전부 걸린다. `--force` 로 강제 검사할 수 있다.

사용:
  python3 tools/lint_style.py <md 파일...> [--style 02-writing-style.md] [--glossary 03-glossary.md] [--warn]

검사 항목
  1. 02-writing-style.md 의 ```lint 블록에 있는 금지 표현
  2. 03-glossary.md 표 왼쪽 열의 사내 용어
  3. 문장 중간 em-dash(—). `- **라벨** — 설명` 불릿, `## 제목 — 부제` 제목, 표 행은 허용
  4. `~기 때문(이다|입니다)` 로 끝나는 문장

매칭 규칙
  - 앞은 한글이 아닌 문자 또는 줄 시작이어야 한다 (구축 ≠ 축)
  - 앞이 숫자면 단위·자릿수로 보고 넘어간다 (8자리, 3축)
  - 뒤는 조사·공백·구두점·줄 끝이어야 한다. 항목이 `*`로 끝나면 뒤 경계를 보지 않는다
  - 코드 펜스 안, `[PLACEHOLDER]` 토큰, HTML 주석은 건너뛴다
종료 코드: 지적이 있으면 1, --warn 이면 항상 0.
"""
import argparse, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(HERE), ".agents", "skills", "job-application-assistant")
RULE_FILES = {"02-writing-style.md", "02-writing-style.template.md",
              "03-glossary.md", "03-glossary.template.md"}
PARTICLES = ("이", "가", "을", "를", "은", "는", "에", "로", "의", "와", "과", "도", "만", "으", "께", "부", "처", "보", "마", "조", "라", "야", "나", "든")
HANGUL = re.compile(r"[가-힣]")


def load_lint_terms(path):
    terms = []
    if not os.path.exists(path):
        return terms
    s = open(path, encoding="utf-8").read()
    m = re.search(r"```lint\n(.*?)```", s, re.S)
    if not m:
        return terms
    for line in m.group(1).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def load_glossary_terms(path):
    terms = []
    if not os.path.exists(path):
        return terms
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        left = cells[0]
        if left in ("사내 용어", "---") or left.startswith("[") or set(left) <= set("-: "):
            continue
        left = re.sub(r"\(.*?\)", "", left).strip()
        if left:
            terms.append(left)
    return terms


def find_term(line, term):
    """term 의 경계 매칭 위치 목록."""
    prefix_only = term.endswith("*")
    t = term.rstrip("*")
    hits = []
    start = 0
    while True:
        i = line.find(t, start)
        if i < 0:
            break
        start = i + 1
        before = line[i - 1] if i > 0 else ""
        after = line[i + len(t)] if i + len(t) < len(line) else ""
        if before and HANGUL.match(before):
            continue
        if before.isdigit():
            continue   # 숫자 뒤는 단위·자릿수다 (8자리, 3축). 은유가 아니다
        if not prefix_only and after and HANGUL.match(after) and not after.startswith(PARTICLES):
            continue
        hits.append(i)
    return hits


ALLOWED_DASH = re.compile(r"^\s*([-*▸•]\s+(\*\*[^*]+\*\*|`[^`]+`)\s+—\s|#{1,6}\s+[^—]+—\s)")
BECAUSE = re.compile(r"기 때문(이다|입니다|이에요|이죠)\s*[.。]?\s*$")


def strip_skips(line):
    line = re.sub(r"<!--.*?-->", "", line)
    line = re.sub(r"\[[A-Z_0-9]+\]", "", line)
    line = re.sub(r"`[^`]*`", "", line)
    return line


def lint_file(path, lint_terms, gloss_terms):
    out = []
    in_fence = False
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = strip_skips(line)
        dash_scope = re.sub(r"\*\*[^*]+\*\*", "", s)  # 굵은 라벨 안의 — 는 식별자 표기로 본다
        if "—" in dash_scope and not s.lstrip().startswith("|") and not ALLOWED_DASH.match(line):
            out.append((n, "em-dash", "문장 중간 부호 꺾기. 마침표로 끊는다"))
        if BECAUSE.search(s):
            out.append((n, "기 때문", "이유를 덧붙이지 말고 사실을 진술한다"))
        for t in lint_terms:
            if find_term(s, t):
                out.append((n, "금지 표현", t.rstrip("*")))
        for t in gloss_terms:
            if find_term(s, t):
                out.append((n, "사내 용어", t))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--style", default=os.path.join(SKILL, "02-writing-style.md"))
    ap.add_argument("--glossary", default=os.path.join(SKILL, "03-glossary.md"))
    ap.add_argument("--warn", action="store_true")
    ap.add_argument("--force", action="store_true", help="규칙 파일도 검사한다")
    a = ap.parse_args(argv)
    lint_terms = load_lint_terms(a.style)
    gloss_terms = load_glossary_terms(a.glossary)
    total = 0
    for f in a.files:
        if not a.force and os.path.basename(f) in RULE_FILES:
            continue
        for n, kind, msg in lint_file(f, lint_terms, gloss_terms):
            print(f"{f}:{n}: [{kind}] {msg}")
            total += 1
    if total:
        print(f"{total}건", file=sys.stderr)
    return 0 if (a.warn or total == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
