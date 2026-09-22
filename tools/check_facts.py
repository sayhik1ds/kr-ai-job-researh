#!/usr/bin/env python3
"""생성 문서의 수치·식별자가 프로필에 있는 값인지 대조한다.

사용:
  python3 tools/check_facts.py <프로필.md> <생성 문서.md ...> [--allow 값 ...]

검사
  - 숫자 토큰(단위 포함. 예: 74%, 10.75초, 107건, 2025.04)이 프로필에 없으면 FAIL
  - 제목 번호("#### 1.1 AMAAQ")와 목록 번호("1. 항목")는 수치로 보지 않는다
  - README.md 는 기본 제외(--include-readme 로 포함)
  - 백틱 식별자(`Spring Boot` 등)가 프로필에 없으면 FAIL (대소문자 무시)
생략은 허용한다. 프로필에 있는 값이 문서에 없어도 실패가 아니다.
--allow 로 예외를 준다 (예: 문서 작성일).
"""
import argparse, os, re, sys

# 단위는 목록으로 고정한다. 한글 1~2자를 탐욕 매칭하면 조사("건의", "초를")까지 먹어 오탐이 난다.
# 긴 단위를 앞에 둔다(개월 > 개, 시간대 > 시간). 단위 뒤 조사("건의", "초를")는 그대로 둔다.
UNITS = r"%|만원|억원|개월|시간대|시간|건|개|명|년|월|일|초|분|주|배|회|종|쪽|줄|장|대|억|만|천|GB|MB|KB|TB|ms|px|kg|cm|mm"
NUM = re.compile(r"(\d+(?:[.,]\d+)*)\s*(" + UNITS + r")?")
SECTION_NO = re.compile(r"^(\s*#{1,6}\s+)\d+(?:\.\d+)*\.?\s+", re.M)
LIST_NO = re.compile(r"^(\s*)\d+\.\s+", re.M)
TICK = re.compile(r"`([^`\n]+)`")


def strip_noise(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"`\[[A-Z_0-9]+\]`", "", text)
    text = re.sub(r"\[[A-Z_0-9]+\]", "", text)
    text = SECTION_NO.sub(r"\1", text)   # "#### 1.1 제목" 의 절 번호는 수치가 아니다
    text = LIST_NO.sub(r"\1", text)      # "1. 항목" 의 목록 번호도 아니다
    return text


def numbers(text):
    out = set()
    for m in NUM.finditer(text):
        n = m.group(1).replace(",", "")
        u = m.group(2) or ""
        out.add(n + u)
        out.add(n)
    return out


def ticks(text):
    return {t.strip().lower() for t in TICK.findall(text)}


def check(profile_text, doc_text, allow=()):
    p = strip_noise(profile_text)
    d = strip_noise(doc_text)
    pn, pt = numbers(p), ticks(p)
    fails = []
    for m in NUM.finditer(d):
        n = m.group(1).replace(",", "")
        u = m.group(2) or ""
        tok = n + u
        if tok in allow or n in allow:
            continue
        if tok in pn or (not u and n in pn):
            continue
        if u and n in pn and n + u not in pn:
            # 숫자는 있는데 단위가 다르다
            fails.append(f"수치 단위 불일치: {tok}")
            continue
        fails.append(f"프로필에 없는 수치: {tok}")
    for t in ticks(d):
        if t not in pt and t not in {a.lower() for a in allow}:
            fails.append(f"프로필에 없는 식별자: `{t}`")
    return sorted(set(fails))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--allow", nargs="*", default=[])
    ap.add_argument("--include-readme", action="store_true", help="README.md 도 대조한다. 기본은 제외(프로파일 기록·공고 id·점수가 들어가는 파일)")
    a = ap.parse_args(argv)
    prof = open(a.profile, encoding="utf-8").read()
    rc = 0
    docs = [f for f in a.docs if a.include_readme or os.path.basename(f).lower() != "readme.md"]
    for f in docs:
        fails = check(prof, open(f, encoding="utf-8").read(), set(a.allow))
        for msg in fails:
            print(f"{f}: {msg}")
        if fails:
            rc = 1
    if rc == 0:
        print("OK: 수치·식별자 모두 프로필에 있음")
    return rc


if __name__ == "__main__":
    sys.exit(main())
