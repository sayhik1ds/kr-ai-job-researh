# JobKorea URL & parameter reference

Observed from jobkorea.co.kr's logged-out web client on 2026-09-22.

## robots.txt (relevant lines)

```
User-agent: *
Disallow: /Search?TS_Search=
Disallow: /Search/?stext=
Allow: /recruit/joblist
Allow: /Recruit/GI_Read
```

Named AI crawlers (GPTBot, ClaudeBot, anthropic-ai, …) get `Disallow: /` with
the same two `Allow` lines. Keyword search is off-limits for everyone.

## Endpoints

| Purpose | Method | URL |
|---|---|---|
| Category list page (human) | GET | `https://www.jobkorea.co.kr/recruit/joblist?menucode=duty` |
| Category list fragment | POST | `https://www.jobkorea.co.kr/Recruit/Home/_GI_List/` |
| Posting page | GET | `https://www.jobkorea.co.kr/Recruit/GI_Read/{id}` |
| Posting body (iframe) | GET | `https://www.jobkorea.co.kr/Recruit/GI_Read_Comt_Ifrm?Gno={id}` |

## List request body (form-encoded)

The site's `jobList.js` posts `{ condition: dataMap, page, pageSize }` with
jQuery's bracket encoding:

```
condition[menucode]=duty
condition[dutyCtgr]=10031        # 대분류
condition[duty]=<codes>          # 소분류, comma-joined (optional)
condition[local]=I000,B000       # 시/도 codes
condition[careerStart]=0
condition[careerEnd]=3
page=1
pageSize=40
```

Send `X-Requested-With: XMLHttpRequest` and a `Referer` of the list page.
A GET to `/recruit/_GI_List` (the pagination href) answers 404; only the POST works.

## List fragment shape

Rows are `<tr class="devloopArea" data-gno="{id}">`:

- `td.tplCo a.link` company name
- `td.tplTit strong a[title]` title, `p.etc span.cell` (career, education, location, employment type in varying order), `p.dsc` summary
- `td.odd span.time` registration hint, `span.date` deadline (`~10/31`)
- `.tplPagination [data-page]` page numbers

## Posting page

Contains a schema.org `JobPosting` block:

```
title, description, datePosted, validThrough, employmentType,
experienceRequirements, educationRequirements,
hiringOrganization.name, jobLocation.address.streetAddress, identifier.value
```

The body is a Next.js `IframeViewer` whose source is `GI_Read_Comt_Ifrm?Gno={id}`.
Some employers upload the body as images; then only the summary block is available.

## Codes seen

대분류 (`dutyCtgr`): 10026 기획·전략, 10027 법무·사무·총무, 10028 인사·HR,
10029 회계·세무, 10030 마케팅·광고·MD, 10031 AI·개발·데이터, 10032 디자인,
10040 엔지니어링·설계, 10044 의료·바이오.

시/도 (`local`): I000 서울, B000 경기, K000 인천, H000 부산, J000 대전, F000 대구.
