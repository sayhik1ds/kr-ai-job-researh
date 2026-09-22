---
name: rank
description: 수집한 공고 전체를 04-job-evaluation.md 기준으로 채점해 순위를 만든다. 사용자가 `/rank` 또는 `$rank`라고 하면 이 스킬을 쓴다.
disable-model-invocation: true
framework_version: 0.1.0
---

# /rank

`/scrape`는 키워드 가중치만 본다. `/rank`는 본문을 읽고 `04-job-evaluation.md` 기준으로 채점한다.

1. `job_scraper/scored_<최근 날짜>_full.json`(본문 기준 채점)에서 상위 N건을 고른다. 스킬 이름 뒤에 숫자를 적으면 N으로 쓴다. 기본 7. 본문이 없는 공고는 먼저 `tools/enrich_jobs.py`로 받는다.
2. 공고마다 서브 에이전트를 동시에 띄운다. 입력은 `job_scraper/details/<포털>_<id>.json`, `01-candidate-profile.md`, `04-job-evaluation.md`, `05-profiles.md`. 웹 검색 금지, 파일 쓰기 금지. 출력은 04-job-evaluation.md의 출력 형식 마크다운 + 아래 JSON 한 블록.
   ```json
   {"key":"<포털>:<id>","company":"","position":"","gate":{"years":"통과|확인 필요|탈락 후보","location":"","stack":""},"scores":{"tech":0,"exp":0,"profile":"","total":0},"verdict":"지원 권장|격차 확인 후 지원|보류|제외","strengths":[],"gaps":[],"due":"","years_required":""}
   ```
3. JSON 블록을 `job_scraper/rank/<포털>_<id>.json`으로 저장한다.
4. `python3 tools/rank_table.py`가 순위표를 출력하고 `job_scraper/rank_<날짜>.json`을 만든다. 게이트 탈락 후보는 표 아래에 따로 나온다.
5. 번호를 고르면 `/apply`로 넘긴다. 연차 게이트가 "확인 필요"인 공고는 그 사실을 한 줄로 다시 알린다.

실행 결과 참고: 2026-09-22 첫 실행에서 7건을 sonnet 서브 에이전트로 동시에 평가했고 건당 1~2분 걸렸다. 인력 대행사 공고(고객사 비공개)는 총점이 높아도 실제 근무사를 알 수 없으니 판정에 그 사실을 적는다.
