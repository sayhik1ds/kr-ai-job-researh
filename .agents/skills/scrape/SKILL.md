---
name: scrape
description: 원티드·점핏·그룹바이·사람인·잡코리아에서 공고를 수집하고 채점해 표로 보여준다. 사용자가 `/scrape` 또는 `$scrape`라고 하면 이 스킬을 쓴다.
disable-model-invocation: true
framework_version: 0.1.0
---

# /scrape

`job-scraper` 스킬의 절차를 따른다. 스킬 이름 뒤에 적은 문자열이 있으면 검색어로 쓴다. 없으면 `search-config.md`의 검색어 전부.

1. 포털 CLI가 설치됐는지 확인한다. `bun run .agents/skills/wanted-search/cli/src/cli.ts search -q "백엔드 개발자" --limit 1 --format json`이 실패하면 `bun install` 안내 후 중단.
2. 수집 → 중복 제거 → 제외 패턴 → 채점 → 표.
3. 표 아래에 "번호를 고르면 /apply로 넘어간다"고 안내한다.
