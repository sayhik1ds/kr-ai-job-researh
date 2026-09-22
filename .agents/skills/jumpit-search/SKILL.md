---
name: jumpit-search
version: 1.0.0
description: >
  Use this skill whenever the user wants to search for developer or IT jobs in
  South Korea, or look up a specific Jumpit (jumpit.saramin.co.kr) posting. Jumpit
  is Saramin's developer-focused Korean job portal and indexes backend, frontend,
  data, AI/ML, DevOps, mobile, embedded and security roles. Invoke for open
  positions, vacancies and hiring in Korea. Trigger phrases: 점핏, 개발자 채용,
  한국 개발자 구인, Korean developer jobs, Seoul engineering jobs, "are there any
  X developer jobs in Korea", look up this Jumpit posting.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/jumpit-search/cli/src/cli.ts *)
---

# Jumpit Search Skill

Search live job listings from Jumpit's public web API. No authentication, no API
key, and **zero runtime dependencies** — it runs with just `bun`.

Jumpit is developer-only, so its result set is narrower and denser than a general
portal's: every posting carries a tech-stack list and an explicit career range.

## ⚠️ Personal use only

This reads Jumpit's public web API, the same endpoints the site calls from a
logged-out browser. Keep request volume low and do not redistribute the results.

## Commands

```bash
# Keyword search (the common case)
bun run .agents/skills/jumpit-search/cli/src/cli.ts search -q "백엔드" --limit 10 --format table

# Newest first, open to 신입
bun run .agents/skills/jumpit-search/cli/src/cli.ts search -q "Spring Boot" --career 0 --sort reg_dt --format json

# Browse one job category, no keyword
bun run .agents/skills/jumpit-search/cli/src/cli.ts search --job-category 1 -n 20 --format json

# One posting in full
bun run .agents/skills/jumpit-search/cli/src/cli.ts detail 55030576 --format plain
bun run .agents/skills/jumpit-search/cli/src/cli.ts detail https://jumpit.saramin.co.kr/position/55030576 --format json
```

### Health-check query

The query below provably worked when this skill was registered. Use it as the
sentinel probe in `/scrape`'s portal health check:

```bash
bun run .agents/skills/jumpit-search/cli/src/cli.ts search -q "백엔드" --limit 3 --format json
```

## Sort keys

| `--sort` | Order |
|---|---|
| `rsp_rate` | Response rate (Jumpit's default; companies that actually reply rank first) |
| `reg_dt` | Newest posting first |
| `popular` | Most viewed |

`rsp_rate` is the default here because a portal-wide scrape is more useful when
non-responding companies sink.

## Output

`--format json` emits `{ meta: { count, page, totalCount }, results: [...] }`.
`totalCount` is how many postings matched the query overall, not just on this
page — useful for deciding whether to paginate.

Each result carries `id`, `title`, `company`, `location`, `date`, `due`, `career`,
`techStacks`, `url`.

`detail` adds `responsibility`, `qualifications`, `preferred`, `welfares`,
`recruitProcess`, and `isActive`. HTML in those fields is stripped to plain text.

## Known limits

- **`date` is null in search results.** The list endpoint carries no published
  timestamp, only `closedAt`. `detail` fills `date` from `publishedAt`. Use
  `--sort reg_dt` when recency matters in a search.
- `isActive` is derived from the deadline, since the payload has no status flag.
  A posting pulled before its `closedAt` is reported active.
- Pagination is 16 per page; `--limit` caps client-side within the fetched page.
