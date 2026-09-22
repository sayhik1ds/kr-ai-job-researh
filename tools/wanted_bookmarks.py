#!/usr/bin/env python3
"""원티드 북마크 공고를 마크다운으로 저장한다.

사용법:
  1. 브라우저에서 wanted.co.kr 로그인 상태로 개발자도구(Network 탭)를 열고
     아무 API 요청의 cookie 헤더를 복사한다. WWW_ONEID_ACCESS_TOKEN 쿠키 하나면 된다.
  2. 저장소 루트 .env 에 적는다 (gitignore 대상):
       WANTED_COOKIE='WWW_ONEID_ACCESS_TOKEN=xxxx'
     또는 환경변수로 준다.
  3. 실행:
       python3 tools/wanted_bookmarks.py

출력 (기본 job_scraper/bookmarks/, WANTED_OUT_DIR 로 변경 가능):
  - {wd_id}_{회사}_{포지션}.md   공고 본문
  - README.md                    인덱스 표
  - ids.json                     북마크된 id 목록. /scrape 가 제외 목록으로 읽는다
  - closed/                      북마크에서 빠진 공고(마감 등)를 옮겨 둔다

참고:
  - 북마크 목록 API(/api/chaos/bookmarks/v1)만 인증 필요.
    공고 상세 API(/api/chaos/jobs/v4/{id}/details)는 인증 없이 응답한다.
"""
import json, os, sys, urllib.request, re, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)


def load_dotenv(path):
    """루트 .env 에서 KEY=VALUE 를 읽어 환경변수에 없는 것만 채운다."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip("'").strip('"')
        os.environ.setdefault(k, v)


load_dotenv(os.path.join(ROOT, ".env"))

# 상대 경로를 주면 저장소 루트 기준으로 해석한다.
OUT_DIR = os.environ.get("WANTED_OUT_DIR") or os.path.join(ROOT, "job_scraper", "bookmarks")
if not os.path.isabs(OUT_DIR):
    OUT_DIR = os.path.join(ROOT, OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

COOKIE = os.environ.get("WANTED_COOKIE", "")

COMMON_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko,en-US;q=0.9,en;q=0.8",
    "referer": "https://www.wanted.co.kr/profile/bookmarks",
    "wanted-user-agent": "user-web",
    "wanted-user-country": "KR",
    "wanted-user-language": "ko",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
}


def http_get_json(url, with_cookie=False):
    req = urllib.request.Request(url, headers=dict(COMMON_HEADERS))
    if with_cookie and COOKIE:
        req.add_header("cookie", COOKIE)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_bookmarks():
    items, offset, limit = [], 0, 20
    while True:
        d = http_get_json(
            f"https://www.wanted.co.kr/api/chaos/bookmarks/v1?limit={limit}&offset={offset}",
            with_cookie=True,
        )
        page = d["data"]
        items += page
        if len(page) < limit:
            return items
        offset += limit


def fetch_job(wd_id):
    return http_get_json(f"https://www.wanted.co.kr/api/chaos/jobs/v4/{wd_id}/details")


def sanitize(s):
    s = re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", s)
    return s.strip()[:80]


def fmt_section(title, body):
    body = (body or "").strip()
    if not body:
        return ""
    return f"## {title}\n\n{body}\n\n"


def build_md(bookmark, detail):
    j = bookmark["job"]
    data = detail["data"]
    dj = data["job"]
    det = dj.get("detail", {}) or {}
    address = j["address"]
    due = dj.get("due_time") or ""
    skills = ", ".join(t.get("title", "") for t in dj.get("skill_tags", []) if t.get("title"))
    attractions = ", ".join(t.get("title", "") for t in dj.get("attraction_tags", []) if t.get("title"))
    # wd_id는 job 안이 아니라 bookmark 최상위에 있다
    url = f"https://www.wanted.co.kr/wd/{bookmark['wd_id']}"
    parts = [
        f"# [{j['company_name']}] {j['position']}\n\n",
        f"- URL: {url}\n",
        f"- 회사: {j['company_name']} (company_id={j['company_id']})\n",
        f"- 위치: {address['country']} {address['location']} / {address['district']} ({address.get('full_location', '')})\n",
        f"- 마감: {due or '상시'}\n",
        f"- 고용형태: {dj.get('employment_type', j.get('employment_type', ''))}\n",
        f"- 보상금: {j['reward'].get('formatted_total', '')} (추천 {j['reward'].get('formatted_recommender', '')} / 합격 {j['reward'].get('formatted_recommendee', '')})\n",
        f"- 북마크: {bookmark['create_time'][:10]}\n",
        f"- 공고확정: {(j.get('confirm_time') or '')[:10]}\n",
    ]
    if skills:
        parts.append(f"- 스킬: {skills}\n")
    if attractions:
        parts.append(f"- 태그: {attractions}\n")
    parts.append("\n")
    parts.append(fmt_section("회사/팀 소개", det.get("intro")))
    parts.append(fmt_section("주요업무", det.get("main_tasks")))
    parts.append(fmt_section("자격요건", det.get("requirements")))
    parts.append(fmt_section("우대사항", det.get("preferred_points")))
    parts.append(fmt_section("혜택 및 복지", det.get("benefits")))
    parts.append(fmt_section("채용 전형", det.get("hire_rounds")))
    return "".join(parts)


def prune_closed(current_ids):
    """현재 북마크에 없는 공고 md를 closed/ 하위로 이동. 재북마크되면 closed/에서 제거."""
    closed_dir = os.path.join(OUT_DIR, "closed")
    moved = []
    for fn in os.listdir(OUT_DIR):
        m = re.match(r"^(\d+)_.+\.md$", fn)
        if not m:
            continue
        if int(m.group(1)) not in current_ids:
            os.makedirs(closed_dir, exist_ok=True)
            shutil.move(os.path.join(OUT_DIR, fn), os.path.join(closed_dir, fn))
            moved.append(fn)
    # 다시 북마크된 공고는 루트에 새로 저장되므로 closed/의 옛 파일은 정리
    if os.path.isdir(closed_dir):
        for fn in os.listdir(closed_dir):
            m = re.match(r"^(\d+)_.+\.md$", fn)
            if m and int(m.group(1)) in current_ids:
                os.remove(os.path.join(closed_dir, fn))
    return moved


def main():
    if not COOKIE:
        print("ERROR: WANTED_COOKIE 가 비어 있다. .env 또는 환경변수로 준다. 파일 상단 사용법 참고.", file=sys.stderr)
        sys.exit(1)

    print("Fetching bookmarks...", file=sys.stderr)
    bms = fetch_bookmarks()
    print(f"Total bookmarks: {len(bms)}", file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        fut2bm = {ex.submit(fetch_job, b["wd_id"]): b for b in bms}
        for fut in as_completed(fut2bm):
            b = fut2bm[fut]
            try:
                detail = fut.result()
                md = build_md(b, detail)
                fn = f"{b['wd_id']}_{sanitize(b['job']['company_name'])}_{sanitize(b['job']['position'])}.md"
                with open(os.path.join(OUT_DIR, fn), "w") as f:
                    f.write(md)
                results.append((b, fn, None))
                print(f"OK  {b['wd_id']} -> {fn}", file=sys.stderr)
            except Exception as e:
                results.append((b, None, str(e)))
                print(f"ERR {b['wd_id']}: {e}", file=sys.stderr)

    results.sort(key=lambda r: r[0]["create_time"], reverse=True)
    idx = [
        "# Wanted 북마크 채용공고 인덱스\n\n",
        f"- 총 {len(bms)}개\n\n",
        "| 회사 | 포지션 | 위치 | 마감 | 북마크 | 파일 |\n",
        "|---|---|---|---|---|---|\n",
    ]
    for b, fn, err in results:
        j = b["job"]
        link = f"[{fn}](./{fn.replace(' ', '%20')})" if fn else f"(실패: {err})"
        idx.append(
            f"| {j['company_name']} | {j['position']} | {j['address']['location']} "
            f"| {(j.get('due_time') or '상시')[:10] if j.get('due_time') else '상시'} "
            f"| {b['create_time'][:10]} | {link} |\n"
        )
    with open(os.path.join(OUT_DIR, "README.md"), "w") as f:
        f.write("".join(idx))
    with open(os.path.join(OUT_DIR, "ids.json"), "w") as f:
        json.dump(sorted(b["wd_id"] for b in bms), f)

    moved = prune_closed({b["wd_id"] for b in bms})
    for fn in moved:
        print(f"CLOSED {fn} -> closed/", file=sys.stderr)

    fails = [r for r in results if r[2]]
    print(f"\nDone: {len(results) - len(fails)} saved, {len(fails)} failed, {len(moved)} moved to closed/. -> {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
