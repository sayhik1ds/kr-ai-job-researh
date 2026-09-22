#!/usr/bin/env python3
"""포털 CLI 출력(JSON)들을 score_jobs.py 입력 스키마 하나로 합친다.

사용:
  python3 tools/merge_jobs.py job_scraper/raw/*.json --out job_scraper/jobs_<날짜>.json
  옵션: --seen job_scraper/seen.json  --bookmarks job_scraper/bookmarks/ids.json

파일 이름 앞부분이 포털 이름이다 (wanted_*, jumpit_*, groupby_*, saramin_*, jobkorea_*).
카드에 본문이 없으므로 `text`는 제목·회사·요약·기술스택·직무 키워드를 합친 것이다.
본문 기반 채점은 /rank 가 상세를 받아서 한다.
"""
import argparse, glob, json, os, re, sys
from datetime import date

PORTALS = ("wanted", "jumpit", "groupby", "saramin", "jobkorea")


def portal_of(path):
    base = os.path.basename(path)
    for p in PORTALS:
        if base.startswith(p + "_") or base == p + ".json":
            return p
    return None


def norm(portal, c):
    cid = str(c.get("id", "")).strip()
    if not cid:
        return None
    parts = [c.get("title") or "", c.get("company") or "", c.get("summary") or ""]
    for k in ("techStacks", "sectors", "positionTypes"):
        v = c.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
    years = c.get("career") or c.get("years") or ""
    return {
        "key": f"{portal}:{cid}",
        "portal": portal,
        "id": cid,
        "company": c.get("company"),
        "position": c.get("title") or c.get("position") or "",
        "years": years,
        "due": c.get("due") or "",
        "location": c.get("location"),
        "url": c.get("url"),
        "text": " ".join(p for p in parts if p),
    }


def load_ids(path):
    if not path or not os.path.exists(path):
        return set()
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("keys") or d.get("ids") or []
    return {str(x) for x in d}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seen", default="job_scraper/seen.json")
    ap.add_argument("--bookmarks", default="job_scraper/bookmarks/ids.json")
    a = ap.parse_args(argv)
    seen = load_ids(a.seen)              # "wanted:123" 형식
    bm = load_ids(a.bookmarks)           # 원티드 wd_id 숫자 목록
    jobs, dup, skipped = {}, 0, 0
    for pattern in a.files:
        for f in sorted(glob.glob(pattern)):
            portal = portal_of(f)
            if portal is None:
                print(f"포털을 알 수 없는 파일 이름: {f}", file=sys.stderr)
                continue
            d = json.load(open(f, encoding="utf-8"))
            for c in d.get("results", []):
                j = norm(portal, c)
                if j is None:
                    continue
                if j["key"] in seen or (portal == "wanted" and j["id"] in bm):
                    skipped += 1
                    continue
                if j["key"] in jobs:
                    dup += 1
                    continue
                jobs[j["key"]] = j
    out = a.out or f"job_scraper/jobs_{date.today().isoformat()}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(list(jobs.values()), fh, ensure_ascii=False, indent=1)
    by = {}
    for j in jobs.values():
        by[j["portal"]] = by.get(j["portal"], 0) + 1
    print(f"합침 {len(jobs)}건 (중복 {dup}, 이미 본 것·북마크 {skipped}) → {out}", file=sys.stderr)
    print("포털별: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
