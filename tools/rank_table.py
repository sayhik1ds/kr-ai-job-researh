#!/usr/bin/env python3
"""job_scraper/rank/*.json (공고별 평가 JSON)을 모아 순위표와 rank_<날짜>.json 을 만든다.

사용: python3 tools/rank_table.py [--dir job_scraper/rank] [--out job_scraper/rank_<날짜>.json]
"""
import argparse, glob, json, os, sys
from datetime import date

ORDER = {"지원 권장": 0, "격차 확인 후 지원": 1, "보류": 2, "제외": 3}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="job_scraper/rank")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rows = []
    for f in sorted(glob.glob(os.path.join(a.dir, "*.json"))):
        try:
            rows.append(json.load(open(f, encoding="utf-8")))
        except Exception as e:
            print(f"읽기 실패 {f}: {e}", file=sys.stderr)
    rows.sort(key=lambda r: (-int(r.get("scores", {}).get("total", 0)), ORDER.get(r.get("verdict"), 9)))
    out = a.out or f"job_scraper/rank_{date.today().isoformat()}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    print("| # | 총점 | 판정 | 회사 | 포지션 | 연차 | 마감 | 격차 요약 |")
    print("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        gaps = "; ".join(r.get("gaps", [])[:2])
        print(f"| {i} | {r['scores']['total']} | {r['verdict']} | {r['company']} | {r['position'][:36]} | {r.get('years_required','')[:14]} | {r.get('due','')} | {gaps[:60]} |")
    gated = [r for r in rows if "탈락" in json.dumps(r.get("gate", {}), ensure_ascii=False)]
    if gated:
        print("\n게이트 탈락 후보: " + ", ".join(f"{r['company']} ({r['key']})" for r in gated))
    print(f"\n→ {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
