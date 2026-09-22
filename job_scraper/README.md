# job_scraper/

`/scrape`로 수집한 공고와 `/rank`로 평가한 결과를 보관하는 폴더다. 수집·평가 자료는 git 추적에서 제외된다.

| 파일 | 내용 |
|---|---|
| `jobs_<날짜>.json` | 수집한 공고. 데이터 형식은 `tools/score_jobs.py` 상단 참고 |
| `scored_<날짜>.json` | 키워드 채점 결과 |
| `rank_<날짜>.json` | `/rank` 결과 |
| `details/<포털>_<id>.json` | 공고 원문 |
| `seen.json` | 이미 본 공고 키 목록 |
| `bookmarks/` | `tools/wanted_bookmarks.py`로 수집한 북마크 |
