# GroupBy URL & data-source reference

Observed from groupby.kr as an anonymous visitor.

## Two sources, one of which lies

| Source | Returns | Use |
|---|---|---|
| `https://groupby.kr/positions` (page, `__NEXT_DATA__`) | Real titles, companies, roles, stacks | **This one** |
| `https://groupby.kr/positions/{id}` (page, `__NEXT_DATA__`) | Real detail metadata | **This one** |
| `https://api.groupby.kr/startup-positions` | Every record masked as `[표시 제한] <직무> (<n>년 이상)` | Never |
| `https://api.groupby.kr/startup-positions/{id}` | Same record, masked | Never |

Evidence that these are the same records and not two different corpora:

```
api.groupby.kr/startup-positions/12218  ->  "[표시 제한] 머신러닝 엔지니어 (4년 이상)"
groupby.kr/positions/12218              ->  "백엔드 엔지니어" / 피트인 / 경력 7~10년
```

The reported totals differ too (`187432` from the API vs `1786` from the page),
so the API's own count cannot be used as a portal size either.

Header variations that do **not** lift the mask, all tested:

```
Referer: https://groupby.kr/positions
Origin: https://groupby.kr
Accept: application/json, text/plain, */*
```

The mask is tied to the caller's identity, not the request shape.

## Page-route limits

`getServerSideProps` hardcodes its SWR fallback key:

```
/startup-positions?isAdvertising=false&limit=10&offset=0&orderBy=-updatedAt
```

`?offset=10`, `?limit=30` and `?search=...` on the page URL are all ignored — the
same 10 newest postings come back every time. There is no anonymous pagination and
no anonymous server-side search.

## `__NEXT_DATA__` shape

**List page** — `props.pageProps.positionFallback` is a map keyed by SWR request
path. Two feeds arrive:

| Key fragment | Meaning |
|---|---|
| `isAdvertising=true` | Sponsored placements. Skipped by this CLI. |
| `isAdvertising=false` | The organic listing. |

Each value is `{ total, items: [...] }`. An item carries:

```
id, name (title), careerType, experienceRange {min,max}, positionTypes[{id,name}],
techStacks[] (plain strings), publishedAt, createdAt, updatedAt, location,
hasCuration, averageReplyPeriod, isInterested
```

**Detail page** — `props.pageProps` has `positionId`, `seoMeta`,
`fallbackDataRaw`, `relatedPositionsFallback`. The posting object is nested inside
`fallbackDataRaw`; this CLI finds it by walking for an object carrying `id`,
`name` and `careerType` rather than pinning a path that a Next.js upgrade would
move. Detail adds `startup` (company), `remoteWorkPreference`, `internPeriod`,
`userApplication`.

Body copy (주요업무, 자격요건, 우대사항) is **not** in the payload on either route.

## Encoding quirks

- `experienceRange` of `{min: 0, max: 20}` means 경력무관/신입, not "0 to 20
  years". The CLI renders `careerType` in that case.
- `techStacks` is an array of plain strings on the list page but the detail page
  keeps the same shape, unlike `positionTypes` which is always `{id, name}`.
- `company` arrives as `startup.name` on the detail page and is absent from list
  items on some feeds.
