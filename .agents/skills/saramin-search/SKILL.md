---
name: saramin-search
version: 1.0.0
description: >
  Use this skill whenever the user wants to search job postings on Saramin
  (saramin.co.kr), Korea's largest general job portal, or look up a specific
  Saramin posting by rec_idx or URL. Covers every sector; filter by experience,
  region and job category. Trigger phrases: 사람인, 사람인 공고, Saramin,
  Korean job search, look up this Saramin posting.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/saramin-search/cli/src/cli.ts *)
---

# Saramin Search Skill

Search Saramin's public result pages and read postings. No authentication, no
API key, **zero runtime dependencies** — runs with just `bun`.

## ⚠️ Personal use only

This reads the same pages a logged-out browser loads. `robots.txt` allows the
search and posting paths for general agents but blocks GPTBot and Bytespider
outright, so keep request volume low and do not redistribute the results.
Saramin's official Open API (`oapi.saramin.co.kr`, access key required) is the
sanctioned route for anything heavier than a personal job search.

## Commands

```bash
# Keyword search, 신입·경력, up to 3 years, Seoul (the common case)
bun run .agents/skills/saramin-search/cli/src/cli.ts search -q "백엔드" --exp 1,2 --exp-max 3 --loc 101000 --limit 10 --format table

# Newest first
bun run .agents/skills/saramin-search/cli/src/cli.ts search -q "Spring Boot" --sort reg_dt --format json

# Category browse plus keyword
bun run .agents/skills/saramin-search/cli/src/cli.ts search -q "AI" --cat 84,235 --page-size 50 --format json

# One posting in full
bun run .agents/skills/saramin-search/cli/src/cli.ts detail 55089251 --format plain
bun run .agents/skills/saramin-search/cli/src/cli.ts detail "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=55089251" --format json
```

### Health-check query

```bash
bun run .agents/skills/saramin-search/cli/src/cli.ts search -q "백엔드 개발자" --limit 3 --format json
```

## Filters

| Flag | Param | Values |
|---|---|---|
| `--exp` | `exp_cd` | `1` 신입, `2` 경력, `99` 경력무관. Comma-join |
| `--exp-min` / `--exp-max` | `exp_min` / `exp_max` | Years |
| `--loc` | `loc_mcd` | `101000` 서울, `102000` 경기, `108000` 인천, `106000` 부산, `105000` 대전, `104000` 대구 |
| `--cat` | `cat_kewd` | `84` 백엔드/서버개발, `235` Java, `272` Python, `92` 프론트엔드, `87` 데이터엔지니어 |
| `--sort` | `recruitSort` | `relation` (default), `reg_dt` |

## Output

`--format json` emits `{ meta: { count, page, totalCount }, results: [...] }`.
`totalCount` is the portal's "총 N건" for the whole query.

Each result carries `id` (rec_idx), `title`, `company`, `location`, `date`,
`due`, `career`, `education`, `employmentType`, `salary`, `sectors`, `url`.

`detail` returns the og: meta summary (`company`, `career`, `education`, `due`
as an ISO date) plus `body`, the posting text with tags stripped, and `isActive`.

## Known limits

- `date` in search results is the list's "수정일 26/09/21" string; `due` is
  "~ 10/25(일)" or "상시채용". `detail` gives the deadline as `YYYY-MM-DD`.
- `detail` has no `location`; the body text usually states it.
- Postings whose body is an image only yield the summary.
- The result page is ~2 MB of HTML per request. Prefer `--page-size 50` over
  many small pages.
