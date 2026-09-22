---
name: wanted-search
version: 1.0.0
description: >
  Use this skill whenever the user wants to search for jobs in South Korea, find
  Korean job listings, or look up a specific Wanted (wanted.co.kr) posting. Wanted
  is Korea's largest startup-and-tech job portal. Invoke for open positions,
  vacancies, and hiring across any sector or role (backend, frontend, data, AI,
  design, marketing, finance, operations, etc.) in Korea. Trigger phrases: 한국
  채용, 원티드, 개발자 채용, find a job in Korea, Korean job search, Seoul jobs,
  "are there any X jobs in Korea", look up this Wanted posting.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/wanted-search/cli/src/cli.ts *)
---

# Wanted Search Skill

Search live job listings from Wanted's public web API. No authentication, no API
key, and **zero runtime dependencies** — it runs with just `bun`.

The API is JSON end to end, so there is no HTML scraping and no parser that breaks
when the markup shifts.

## ⚠️ Personal use only

This reads Wanted's public web API, the same endpoints the site itself calls from a
logged-out browser. Keep request volume low and do not redistribute the results.

## Commands

```bash
# Keyword search (the common case)
bun run .agents/skills/wanted-search/cli/src/cli.ts search -q "백엔드 개발자" --limit 10 --format table

# Narrow by years of experience
bun run .agents/skills/wanted-search/cli/src/cli.ts search -q "Spring Boot" --years-min 0 --years-max 3 --format json

# Category browse, no keyword (개발 job group, backend/web/software categories)
bun run .agents/skills/wanted-search/cli/src/cli.ts search --job-group 518 --job-ids 660,872,873 --years-min 0 --years-max 3 -n 20 --format json

# One posting in full
bun run .agents/skills/wanted-search/cli/src/cli.ts detail 379643 --format plain
bun run .agents/skills/wanted-search/cli/src/cli.ts detail https://www.wanted.co.kr/wd/379643 --format json
```

### Health-check query

The query below provably worked when this skill was registered. Use it as the
sentinel probe in `/scrape`'s portal health check:

```bash
bun run .agents/skills/wanted-search/cli/src/cli.ts search -q "백엔드 개발자" --limit 3 --format json
```

## Keyword search vs category browse

These are **different endpoints**, and the difference matters:

| Flag | Endpoint | Behaviour |
|---|---|---|
| `--query` | `/api/chaos/search/v1/results` | Honours the keyword. Jobs arrive under `positions.data`. |
| `--job-group` / `--job-ids` | `/api/chaos/navigation/v1/results` | Category browse. **Ignores `query` silently** — passing a keyword here returns the unfiltered category feed, which looks like a working search but is not. |

The CLI picks the right endpoint for you: give it `--query` and it searches; omit
`--query` and it browses the category you named.

## Job category ids

`--job-group 518` is 개발 (development). Useful `--job-ids` within it:

| id | Category |
|---|---|
| 660 | 서버/백엔드 개발자 |
| 872 | 웹 개발자 |
| 873 | 소프트웨어 엔지니어 |

Other groups and ids are listed in [`url-reference.md`](url-reference.md).

## Output

`--format json` emits `{ meta: { count, page }, results: [...] }`. Each result
carries `id`, `title`, `company`, `location`, `due`, `employmentType`, `url` —
enough for `/scrape` to build a dedup key via `tools/job_key.py`.

`detail` adds `intro`, `mainTasks`, `requirements`, `preferred`, `benefits`,
`skills`, and `isActive`. HTML in those rich-text fields is stripped to plain text.

## Known limits

- `due` is `상시채용` for most postings; Wanted rarely sets a real deadline.
- Pagination is 20 per page; `--limit` caps client-side within the fetched page.
- A closed posting returns 404 on `detail` and exits 1 with `NOT_FOUND`.
