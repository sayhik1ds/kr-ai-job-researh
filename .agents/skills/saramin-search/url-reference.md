# Saramin URL & parameter reference

Observed from saramin.co.kr's logged-out web client on 2026-09-22.

## robots.txt (relevant lines)

```
User-agent: GPTBot      Disallow: /
User-agent: Bytespider  Disallow: /
User-agent: *
Disallow: /zf_user/recruit/recruit-posting/
Disallow: /recruit/recruit_view.php
```

`/zf_user/search/recruit` and `/zf_user/jobs/...` are not disallowed for `*`.

## Endpoints

| Purpose | URL |
|---|---|
| Search | `https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=…` |
| Posting page (og: meta) | `https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={id}` |
| Posting body | `https://www.saramin.co.kr/zf_user/jobs/relay/view-detail?rec_idx={id}&rec_seq=0` |
| Human-readable posting | `https://www.saramin.co.kr/zf_user/jobs/view?rec_idx={id}` |

## Search query parameters

| Param | Notes |
|---|---|
| `searchType` | `search` |
| `searchword` | Free text |
| `recruitPage` | 1-indexed |
| `recruitPageCount` | Results per page. 20 by default, 100 accepted |
| `recruitSort` | `relation`, `reg_dt` |
| `exp_cd` | `1` 신입, `2` 경력, `99` 경력무관. Comma-join |
| `exp_min` / `exp_max` | Years |
| `loc_mcd` | 시/도 code. `101000` 서울, `102000` 경기 … (district codes are `loc_cd`) |
| `cat_kewd` | Job keyword category. `84` 백엔드/서버개발, `235` Java, `272` Python. See the table below for other fields |

Total count: `<span class="cnt_result">총 2,638건</span>`.

## Result item shape

Each posting is `<div class="item_recruit" value="{rec_idx}">` with:

- `h2.job_tit a[title]` title
- `div.job_condition span` × N: location, career (`경력 5~10년` / `신입` / `경력무관`), education (`초대졸↑`), employment type, sometimes salary
- `div.job_sector a` job keywords, `span.job_day` "수정일 26/09/21"
- `div.area_corp strong.corp_name a[title]` company
- `div.job_date span.date` "~ 10/25(일)"

## Posting page

The page itself renders the body client-side. Two things are usable:

- `og:title` = `[회사] 제목(D-33) - 사람인`
- `og:description` = `회사, 제목, 경력:경력 5~10년, 학력:대학졸업(2,3년)이상, 면접 후 결정, 마감일:2026-10-25, 홈페이지:…`

The body endpoint `view-detail?rec_idx=…&rec_seq=0` returns server-rendered HTML
of the posting (intro, 주요업무, 자격요건, 우대사항, 근무조건, 전형절차).

## `cat_kewd` beyond software

Saramin serves `/zf_user/jobs/list/job-category` as a Handlebars template and
fills it over XHR, so there is no single endpoint that lists every code. The
practical way to find one is to search for the job title, then read the
`cat_kewd` values out of the `div.job_sector` links on the result cards.

Codes collected that way on 2026-09-22. All 44 below were then re-checked
against a fresh set of searches: every id rendered the same label Saramin
itself prints on the result cards, with no mismatches, and each returns a
non-empty result set when passed alone. The labels are Saramin's own link
text, which is the only taxonomy the public pages expose.

| Field | Codes |
|---|---|
| 마케팅·광고 | 1412 마케팅기획, 1425 디지털마케팅, 1429 브랜드마케팅, 1435 콘텐츠마케팅, 1437 퍼포먼스마케팅, 1419 SNS마케팅, 1626 광고기획, 1449 검색광고 |
| 디자인 | 1484 그래픽디자인, 1496 시각디자인, 1493 브랜드디자인, 1502 웹디자인, 1529 UI/UX디자인, 1515 콘텐츠디자인, 1500 영상디자인 |
| 영업 | 699 영업관리, 700 영업지원, 764 기업영업, 746 해외영업, 692 기술영업, 2208 영업기획 |
| 기획·PM | 1635 서비스기획, 1637 웹기획, 1633 사업기획, 1639 전략기획, 1649 PM(프로젝트매니저), 1634 상품기획 |
| 인사 | 2198 인사, 449 인사행정, 448 인사기획, 438 HRM, 439 급여(Payroll), 396 총무 |
| 재무·회계 | 2220 재무, 2197 회계, 366 재무회계, 338 관리회계, 371 회계결산, 360 자금관리 |
| 데이터 분석 | 82 데이터분석가, 1658 데이터분석, 2248 데이터 사이언티스트, 116 빅데이터, 107 데이터시각화 |

Two caveats.

- **Duplicate names carry different codes** (1440 and 1318 both render as
  AE(광고기획자); 1412 and 1629 both as 마케팅기획). Legacy and current keyword
  sets appear to coexist. Passing both codes is safer than guessing.
- **A category filter alone surfaces mass-hiring posts.** Large postings tag
  themselves with dozens of categories, so they rank top for many codes.
  Combine `cat_kewd` with `searchword`, or filter the titles client-side.
