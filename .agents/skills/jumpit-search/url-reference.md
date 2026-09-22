# Jumpit URL & parameter reference

Observed from jumpit.saramin.co.kr's logged-out web client. No authentication is
required for any endpoint below.

## Endpoints

| Purpose | URL |
|---|---|
| Search / browse | `https://jumpit-api.saramin.co.kr/api/positions` |
| Posting detail | `https://jumpit-api.saramin.co.kr/api/position/{id}` |
| Human-readable posting | `https://jumpit.saramin.co.kr/position/{id}` |

Two traps in that table:

- **Singular vs plural.** The list is `/api/positions`; the detail is
  `/api/position/{id}`. `/api/positions/{id}` answers 404.
- **Host.** `api.jumpit.co.kr` answers 301 and is not the live API.
  `jumpit-api.saramin.co.kr` is.

## Query parameters

| Param | Notes |
|---|---|
| `keyword` | Free-text search across title, company and stack. |
| `jobCategory` | Job-category id, repeatable. |
| `techStack` | Tech-stack id, repeatable. |
| `career` | Minimum years of experience. `0` = 신입. |
| `sort` | `rsp_rate` (응답률), `reg_dt` (최신), `popular` (인기). |
| `page` | 1-indexed. 16 results per page. |

## Response shapes

**List** wraps results as:

```
{ message, status, code, result: { totalCount, page, keyword, keywordType, positions: [...] } }
```

A position object in the list:

```
id, title, companyName, jobCategory (comma-joined string), techStacks[],
locations[], minCareer, maxCareer, newcomer, alwaysOpen, closedAt,
viewCount, celebration, serialNumber, encodedSerialNumber
```

**Detail** is `{ result: { ... } }` with a different field set:

```
id, title, companyName, techStacks[], serviceInfo, responsibility,
qualifications, preferredRequirements, welfares, recruitProcess,
newcomer, minCareer, maxCareer, publishedAt, closedAt, location (singular), tags
```

Differences that matter when normalizing the two into one shape:

- list has `locations` (array); detail has `location` (single string)
- `publishedAt` exists **only** on detail, so search results have no posting date
- `closedAt` is `2026-10-13T23:59:59` on the list and `2026-10-13 23:59:59` on the
  detail; both are truncated to the date
- there is no status flag anywhere, so "is this still open" has to be derived
  from `closedAt`

## Job category ids

| id | Category |
|---|---|
| 1 | 서버/백엔드 개발자 |
| 2 | 프론트엔드 개발자 |
| 3 | 웹 풀스택 개발자 |
| 4 | 안드로이드 개발자 |
| 5 | iOS 개발자 |
| 9 | devops/시스템 엔지니어 |
| 11 | 데이터 엔지니어 |
| 12 | 인공지능/머신러닝 |
| 16 | QA 엔지니어 |

To find an id not listed here, apply the filter on jumpit.saramin.co.kr and read
`jobCategory` out of the resulting URL.
