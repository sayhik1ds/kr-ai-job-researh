#!/usr/bin/env python3
"""수집한 공고를 키워드 가중치로 채점한다.

사용:
  python3 tools/score_jobs.py <jobs.json> [--config search-config.md] [--min-score N] [--out scored.json]

입력 스키마 (jobs.json, 리스트)
  {
    "key": "wanted:379643",       # <포털>:<id>
    "portal": "wanted",
    "id": "379643",
    "company": "회사명",
    "position": "포지션명",
    "years": "0~3",               # 없으면 ""
    "due": "2026-10-31",          # 없으면 "상시"
    "url": "https://...",
    "text": "소개 + 주요 업무 + 자격 요건 + 우대 사항 전체 본문"
  }

search-config.md 에서 읽는 블록
  ```drop     제목 제외 정규식 (한 줄에 하나, | 로 합침)
  ```weights  `키워드 = 정수` (# 주석)
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(os.path.dirname(HERE), ".agents", "skills", "job-scraper", "search-config.md")


def parse_config(text):
    drop, weights = [], {}
    m = re.search(r"```drop\n(.*?)```", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("["):
                drop.append(line)
    m = re.search(r"```weights\n(.*?)```", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            k, _, v = line.partition("=")
            k, v = k.strip().lower(), v.strip()
            if k and re.fullmatch(r"-?\d+", v):
                weights[k] = int(v)
    drop_re = re.compile("|".join(drop), re.I) if drop else None
    return drop_re, weights


def score(job, weights):
    text = (job.get("position", "") + " " + job.get("text", "")).lower()
    total, hits = 0, []
    for k, w in weights.items():
        if k in text:
            total += w
            hits.append(k if w >= 0 else f"-{k}")
    return total, hits


def run(jobs, drop_re, weights):
    out, dropped = [], []
    for j in jobs:
        if drop_re and drop_re.search(j.get("position", "")):
            dropped.append(j)
            continue
        s, h = score(j, weights)
        out.append({**j, "score": s, "hits": h})
    out.sort(key=lambda r: -r["score"])
    return out, dropped


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--min-score", type=int, default=10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    drop_re, weights = parse_config(open(a.config, encoding="utf-8").read())
    if not weights:
        print("weights 블록이 비어 있다. /setup --section search 로 채운다", file=sys.stderr)
    jobs = json.load(open(a.jobs, encoding="utf-8"))
    scored, dropped = run(jobs, drop_re, weights)
    out = a.out or a.jobs.replace("jobs_", "scored_")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=1)
    print(f"채점 {len(scored)}건, 제외 {len(dropped)}건 → {out}", file=sys.stderr)
    for r in scored:
        if r["score"] >= a.min_score:
            print(f'{r["score"]:>3} | {r.get("key","")} | {r.get("due","")} | {r.get("years","")} | '
                  f'{r.get("company","")} | {r.get("position","")} | {",".join(r["hits"])}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
