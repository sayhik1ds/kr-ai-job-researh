---
name: jobkorea-search
version: 1.0.0
description: >
  Use this skill to browse developer and IT postings on JobKorea (jobkorea.co.kr),
  one of Korea's two largest general job portals, or to read a specific JobKorea
  posting by id or URL. Browses by category, region and career range; keyword
  matching is client-side. Trigger phrases: 잡코리아, 잡코리아 공고, JobKorea,
  Korean job portal, look up this JobKorea posting.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/jobkorea-search/cli/src/cli.ts *)
---

# JobKorea Search Skill

Browse JobKorea's public category list and read postings. No authentication, no
API key, **zero runtime dependencies** — runs with just `bun`.

## ⚠️ Access rules and personal use

JobKorea's `robots.txt` (updated 2026-04) **disallows `/Search/?stext=` for every
user agent** and restricts named AI crawlers to a short allow-list that includes
`/recruit/joblist` and `/Recruit/GI_Read`. This skill therefore:

- never calls the keyword-search endpoint. `-q` filters the category list on the
  client, so widen with `--pages` when a keyword matters.
- only reads the category list and posting pages a logged-out browser would load.

Keep request volume low. Do not redistribute the results.

## Commands

```bash
# Developer postings in Seoul, 0~3 years (the common case)
bun run .agents/skills/jobkorea-search/cli/src/cli.ts search --local I000 --career-min 0 --career-max 3 --limit 20 --format table

# Keyword narrowing over three pages
bun run .agents/skills/jobkorea-search/cli/src/cli.ts search -q "백엔드|서버|Spring" --local I000,B000 --pages 3 --format json

# One posting in full (ld+json summary + posting body)
bun run .agents/skills/jobkorea-search/cli/src/cli.ts detail 50038225 --format plain
bun run .agents/skills/jobkorea-search/cli/src/cli.ts detail https://www.jobkorea.co.kr/Recruit/GI_Read/50038225 --format json
```

### Health-check query

```bash
bun run .agents/skills/jobkorea-search/cli/src/cli.ts search --limit 3 --format json
```

## Filters

| Flag | Values |
|---|---|
| `--duty-ctgr` | 대분류. `10031` AI·개발·데이터 (default), `10040` 엔지니어링·설계, `10026` 기획·전략 |
| `--duty` | Sub-duty codes if you know them. Passed through unchanged |
| `--local` | `I000` 서울, `B000` 경기, `K000` 인천, `H000` 부산, `J000` 대전, `F000` 대구. Comma-join for several |
| `--career-min` / `--career-max` | Years. `0` includes 신입 |

## Output

`--format json` emits `{ meta: { count, page, pages, lastPage }, results: [...] }`.
`lastPage` is the highest page number the site's pagination showed for the
filter, so you can decide how far `--pages` should go.

Each result carries `id`, `title`, `company`, `location`, `date`, `due`,
`career`, `education`, `employmentType`, `summary`, `url`.

`detail` adds `address`, `body` (posting text with tags stripped) and
`isActive`. Summary fields come from the page's schema.org `JobPosting` block.

## Known limits

- **No server-side keyword search** (see access rules above).
- `date` and `due` in search results are the list's display strings
  (`"4분 전 등록"`, `"~10/31"`), not ISO dates. `detail` gives ISO dates.
- Sub-duty codes are loaded lazily by the site and are not enumerated here.
  Category-level filtering plus `-q` covers the developer case.
- Postings whose body is an image only yield the schema.org summary.
