---
name: groupby-search
version: 1.0.0
description: >
  Use this skill to see what is newly posted on GroupBy (groupby.kr), a Korean
  startup job board, or to look up a specific GroupBy posting by id or URL.
  GroupBy curates startup roles across engineering, product, design, marketing,
  sales and operations. Invoke for Korean startup hiring and for resolving a
  groupby.kr/positions/<id> link. Trigger phrases: 그룹바이, 스타트업 채용,
  Korean startup jobs, look up this GroupBy posting. Note the narrow search
  scope described below before relying on it for a portal-wide sweep.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/groupby-search/cli/src/cli.ts *)
---

# GroupBy Search Skill

Read job postings from GroupBy's server-rendered pages. No authentication, no API
key, and **zero runtime dependencies** — it runs with just `bun`.

## ⚠️ Do not switch this to api.groupby.kr

`api.groupby.kr/startup-positions` answers **HTTP 200 with well-formed JSON** for
an anonymous caller, so it looks like the obvious data source and passes a naive
smoke test. Every record it returns is masked:

```
GET api.groupby.kr/startup-positions/12218  ->  "[표시 제한] 머신러닝 엔지니어 (4년 이상)"
GET groupby.kr/positions/12218              ->  "백엔드 엔지니어", 피트인, 7~10년, 11 tech stacks
```

Same id, same record. The title, company, role and years are all replaced for
unauthenticated API callers, and `Referer` / `Origin` / `Accept` headers do not
lift it. A skill built on that endpoint feeds fabricated postings into `/scrape`
and `/rank` while every health check stays green.

This CLI parses the page's `__NEXT_DATA__` instead, and both `search` and `detail`
refuse to emit anything containing `표시 제한` (exit 1, `MASKED_SOURCE`).

## ⚠️ Search scope is one page

GroupBy server-renders only the newest page of its feed — **10 postings** — and
ignores `limit` / `offset` in the page URL. There is no anonymous server-side
keyword search.

So `--query` filters **client-side over those 10**. Treat `search` as a "what is
new on GroupBy" probe, not a portal-wide sweep. `meta.totalCount` reports how many
postings the feed claims overall (≈1,780) against `meta.fetched` (10), so the gap
is visible in the output rather than implied.

`detail` has no such limit and works for any posting id.

## Commands

```bash
# What is newly posted
bun run .agents/skills/groupby-search/cli/src/cli.ts search --format table

# Filter that page
bun run .agents/skills/groupby-search/cli/src/cli.ts search -q "백엔드" --format json

# One posting
bun run .agents/skills/groupby-search/cli/src/cli.ts detail 12218 --format plain
bun run .agents/skills/groupby-search/cli/src/cli.ts detail https://groupby.kr/positions/12218 --format json
```

### Health-check query

The query below provably worked when this skill was registered. Use it as the
sentinel probe in `/scrape`'s portal health check:

```bash
bun run .agents/skills/groupby-search/cli/src/cli.ts search --limit 3 --format json
```

It takes no keyword on purpose: a `--query` that happens to match none of the
current 10 postings would read as a broken portal.

## Output

`--format json` emits `{ meta: { count, fetched, totalCount, note }, results: [...] }`.

Each result carries `id`, `title`, `company`, `location`, `date`, `due`, `career`,
`positionTypes`, `techStacks`, `url`. `date` comes from `publishedAt`.

`detail` adds `remoteWork`, `internPeriod`, `averageReplyPeriod`, `isActive`.

## Known limits

- **No posting body.** GroupBy does not put 주요업무/자격요건 in the rendered
  payload, so `detail` returns structured metadata and the URL, not prose. Fetch
  the URL when `/apply` needs the full text.
- `due` is always null; GroupBy postings carry no application deadline.
- `location` is frequently null on the list feed.
- `isActive` is true whenever the page renders, since there is no status flag.
