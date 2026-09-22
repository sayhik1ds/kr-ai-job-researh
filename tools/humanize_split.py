#!/usr/bin/env python3
"""마크다운에서 산문 단락만 뽑아 휴머나이저에 넘기고, 결과를 제자리로 되돌린다.

휴머나이저는 산문용이다. 명사형 종결 불릿(`개발`, `구축`)과 수치 행에 걸면 문체가 망가진다.
이 도구가 형태로 구분한다. 문장형 산문만 뽑고 불릿·표·코드·제목·트리는 건드리지 않는다.

  # 1) 뽑기
  python3 tools/humanize_split.py split applications/<회사>_<포지션>/이력서.md \
      --out _workspace/humanize_이력서.md --map _workspace/humanize_이력서.json

  # 2) 휴머나이저에 --out 파일을 넘긴다. 결과는 final.md
  #    요약 주석(<!-- HUMANIZE-SUMMARY -->)은 넣지 말라고 지시한다. 블록 매핑이 깨진다.

  # 3) 되돌리기 (--check 는 수치·코드·링크 보존 검사)
  python3 tools/humanize_split.py merge applications/<회사>_<포지션>/이력서.md \
      --final _workspace/<run_id>/final.md --map _workspace/humanize_이력서.json --check

되돌리기는 `--in-place` 가 없으면 `<원본>.humanized.md` 로 쓴다.
"""
import argparse, json, os, re, sys

MIN_LEN = 20
SKIP_PREFIX = ("#", "|", "-", "*", "+", "▸", "•", "├", "│", "└", "─", "=")
FENCE = re.compile(r"^\s*(```|~~~)")
NUMBERED = re.compile(r"^\s*\d+[.)]\s")
BOLD_LABEL = re.compile(r"^\s*\*\*[^*]+\*\*\s")     # "**기간** 2026.04" 같은 라벨 줄
HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
QUOTE = re.compile(r"^(\s*>\s?)(.*)$")


def classify(line):
    """(산문인가, 접두사) 를 돌려준다. 접두사는 되돌릴 때 복원한다."""
    if not line.strip():
        return False, ""
    if HR.match(line):
        return False, ""
    m = QUOTE.match(line)
    if m:                                   # 인용 블록은 산문이다 (이력서 한 줄 소개, 프로젝트 배경)
        body = m.group(2)
        return (len(body.strip()) >= 1), m.group(1)
    t = line.lstrip()
    if t[0] in SKIP_PREFIX or NUMBERED.match(line) or BOLD_LABEL.match(line):
        return False, ""
    return True, ""


def split_blocks(text):
    """[(start, end, prefix, body)] 를 돌려준다. 연속한 산문 줄이 한 블록이다."""
    lines = text.split("\n")
    blocks, cur, start, prefix, fence = [], [], None, "", False
    def flush(end):
        nonlocal cur, start, prefix
        if cur and len("\n".join(cur).strip()) >= MIN_LEN:
            blocks.append((start, end, prefix, "\n".join(cur)))
        cur, start, prefix = [], None, ""
    for i, ln in enumerate(lines):
        if FENCE.match(ln):
            flush(i - 1)
            fence = not fence
            continue
        if fence:
            flush(i - 1)
            continue
        is_prose, pre = classify(ln)
        if is_prose:
            if start is None:
                start, prefix = i, pre
            elif pre != prefix:             # 인용과 평문이 섞이면 블록을 끊는다
                flush(i - 1)
                start, prefix = i, pre
            cur.append(ln[len(pre):] if pre else ln)
        else:
            flush(i - 1)
    flush(len(lines) - 1)
    return blocks


def parse_marked(text):
    out, parts = {}, re.split(r"^<!--\s*§(\d+)\s*-->\s*$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        out[int(parts[i])] = parts[i + 1].strip("\n")
    return out


def tokens(s):
    return {
        "code": sorted(re.findall(r"`([^`\n]+)`", s)),
        "link": sorted(re.findall(r"\]\(([^)]+)\)", s)),
        "num": sorted(re.findall(r"\d[\d,.]*\s*[가-힣%A-Za-z]{0,3}", s)),
    }


def cmd_split(a):
    text = open(a.file, encoding="utf-8").read()
    blocks = split_blocks(text)
    if not blocks:
        print("산문 블록이 없다", file=sys.stderr)
        return 1
    body, meta = [], []
    for n, (s, e, pre, t) in enumerate(blocks, 1):
        body += [f"<!-- §{n} -->", t, ""]
        meta.append({"n": n, "start": s, "end": e, "prefix": pre})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(body))
    json.dump({"source": os.path.relpath(a.file), "blocks": meta},
              open(a.map, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    chars = sum(len(b[3]) for b in blocks)
    print(f"산문 {len(blocks)}블록 {chars}자 → {a.out} (매핑 {a.map})", file=sys.stderr)
    if chars > 5000:
        print("5,000자를 넘는다. 휴머나이저가 정밀 모드로 승급하니 문서를 나눠 돌린다", file=sys.stderr)
    return 0


def cmd_merge(a):
    orig = open(a.file, encoding="utf-8").read()
    lines = orig.split("\n")
    m = json.load(open(a.map, encoding="utf-8"))
    new = parse_marked(open(a.final, encoding="utf-8").read())
    meta = m["blocks"]
    missing = [b["n"] for b in meta if b["n"] not in new]
    if missing:
        print(f"FAIL: final.md 에 없는 블록 {missing}", file=sys.stderr)
        return 1
    out, changed = list(lines), 0
    for b in sorted(meta, key=lambda x: -x["start"]):   # 뒤에서부터 바꿔야 줄 번호가 안 밀린다
        pre, repl = b["prefix"], new[b["n"]]
        before = "\n".join(lines[b["start"]:b["end"] + 1])
        after = "\n".join(pre + ln if ln.strip() else pre.rstrip() for ln in repl.split("\n"))
        if before.strip() != after.strip():
            changed += 1
            if a.diff:
                print(f"--- §{b['n']} (줄 {b['start']+1}~{b['end']+1})")
                print(f"  - {before.strip()[:150]}")
                print(f"  + {after.strip()[:150]}")
        out[b["start"]:b["end"] + 1] = after.split("\n")
    merged = "\n".join(out)
    if a.check:
        ta, tb = tokens(orig), tokens(merged)
        bad = [k for k in ta if ta[k] != tb[k]]
        for k in bad:
            only_a = [x for x in ta[k] if x not in tb[k]][:5]
            only_b = [x for x in tb[k] if x not in ta[k]][:5]
            print(f"FAIL {k}: 원본에만 {only_a} / 윤문본에만 {only_b}", file=sys.stderr)
        if bad:
            return 1
        print(f"OK 코드·링크·수치 토큰 보존 ({len(ta['code'])}·{len(ta['link'])}·{len(ta['num'])}개)", file=sys.stderr)
    dest = a.file if a.in_place else a.file.replace(".md", ".humanized.md")
    open(dest, "w", encoding="utf-8").write(merged)
    print(f"{len(meta)}블록 중 {changed}개 변경 → {dest}", file=sys.stderr)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("split"); p.add_argument("file"); p.add_argument("--out", required=True); p.add_argument("--map", required=True)
    q = sub.add_parser("merge"); q.add_argument("file"); q.add_argument("--final", required=True); q.add_argument("--map", required=True)
    q.add_argument("--check", action="store_true"); q.add_argument("--diff", action="store_true"); q.add_argument("--in-place", action="store_true")
    a = ap.parse_args(argv)
    return cmd_split(a) if a.cmd == "split" else cmd_merge(a)


if __name__ == "__main__":
    sys.exit(main())
