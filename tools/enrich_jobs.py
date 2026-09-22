#!/usr/bin/env python3
"""채점 상위 공고의 본문을 포털 CLI `detail`로 받아 `text`에 붙이고 저장한다.

사용:
  python3 tools/enrich_jobs.py job_scraper/scored_<날짜>.json --top 60 --out job_scraper/jobs_<날짜>_full.json

본문은 job_scraper/details/<portal>_<id>.json 에 원문 그대로 둔다. 이미 있으면 다시 받지 않는다.
끝나면 score_jobs.py 를 다시 돌려 본문 기준으로 채점한다.
"""
import argparse, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = {p: os.path.join(ROOT, ".agents", "skills", f"{p}-search", "cli", "src", "cli.ts")
       for p in ("wanted", "jumpit", "groupby", "saramin", "jobkorea")}
BODY_KEYS = ("intro", "mainTasks", "requirements", "preferred", "benefits", "responsibility",
             "qualifications", "welfares", "recruitProcess", "description", "body", "summary", "text")


def fetch_detail(portal, jid):
    path = os.path.join(ROOT, "job_scraper", "details", f"{portal}_{jid}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    r = subprocess.run(["bun", "run", CLI[portal], "detail", jid, "--format", "json"],
                       capture_output=True, text=True, timeout=60, cwd=ROOT)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    d = json.loads(r.stdout)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return d


def body_text(d):
    parts = []
    for k in BODY_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    for k in ("techStacks", "sectors"):
        v = d.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("scored")
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument("--out", default=None)
    ap.add_argument("--sleep", type=float, default=0.7)
    a = ap.parse_args(argv)
    jobs = json.load(open(a.scored, encoding="utf-8"))
    targets = jobs[: a.top]
    ok = fail = 0
    for j in targets:
        d = fetch_detail(j["portal"], j["id"])
        if d is None:
            fail += 1
            continue
        j["text"] = (j.get("text") or "") + "\n" + body_text(d)
        if d.get("due"):
            j["due"] = d["due"]
        if d.get("career"):
            j["years"] = d["career"]
        j["has_body"] = True
        ok += 1
        time.sleep(a.sleep)
    out = a.out or a.scored.replace("scored_", "jobs_").replace(".json", "_full.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=1)
    print(f"본문 수집 {ok}건, 실패 {fail}건 → {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
