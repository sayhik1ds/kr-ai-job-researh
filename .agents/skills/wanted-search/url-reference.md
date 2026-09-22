# Wanted URL & parameter reference

Observed from wanted.co.kr's logged-out web client. No authentication is required
for any endpoint below.

## Endpoints

| Purpose | URL |
|---|---|
| Keyword search | `https://www.wanted.co.kr/api/chaos/search/v1/results` |
| Category browse | `https://www.wanted.co.kr/api/chaos/navigation/v1/results` |
| Posting detail | `https://www.wanted.co.kr/api/chaos/jobs/v4/{id}/details` |
| Human-readable posting | `https://www.wanted.co.kr/wd/{id}` |

## Required headers

Wanted keys response language off these. Without them some fields come back in
English and the Korean position title can be omitted.

```
wanted-user-country: KR
wanted-user-language: ko
wanted-user-agent: user-web
```

## Query parameters

| Param | Applies to | Notes |
|---|---|---|
| `query` | search only | The keyword. **Silently ignored by the navigation endpoint.** |
| `job_group_id` | navigation | Parent category. `518` = 개발. |
| `job_ids` | navigation | Child category, repeatable (`&job_ids=660&job_ids=872`). |
| `years` | both | Repeat twice for a range: `&years=0&years=3` = 0–3 years. |
| `locations` | both | `all`, or a code such as `seoul.all`. |
| `country` | both | `kr`. |
| `job_sort` | both | `job.latest_order` (newest) or `job.recommend_order`. |
| `limit` / `offset` | both | Page size and start index. 20 is the site default. |

## Response shapes

**Search** returns a bundle; jobs are under `positions.data`. Sibling keys
(`companies`, `careers`, `social_posts`, `profiles`) are other search verticals and
are not job postings.

**Navigation** returns the same position objects at the top level under `data`.

A position object carries:

```
id, position (title), company.name, address.{country,location,district},
due_time, employment_type, category_tag.{parent_id,id}, skill_tags[]
```

**Detail** nests differently and this is the one real trap:

- the job title is on `data.job.detail.position`, **not** on `data.job.position`
- `data.job.name` is `null` for the postings observed
- skill tags carry their label on `text`, not `title`
- body copy splits across `detail.intro`, `detail.main_tasks`,
  `detail.requirements`, `detail.preferred_points`, `detail.benefits`, all HTML

## Job groups (`job_group_id`)

The full category tree ships in the `__NEXT_DATA__` blob of
`https://www.wanted.co.kr/wdlist`, under `props.pageProps.tags.category`. One
request returns every group and sub-category with its current open-job count.
Numbers below were read on 2026-09-22 and drift over time; the ids do not.

All 20 ids were verified on 2026-09-22 by querying each one and reading the
titles that came back. An id the site does not know returns an empty result
set rather than falling back to an unfiltered search, so a non-empty response
is evidence the filter applied. Note that `514` carried a `counts.job` of 0 in
the tree yet still returns postings; treat the counts as indicative, not exact.

| id | Group | Open jobs | Sub-categories |
|---|---|---|---|
| 518 | 개발 | 4202 | 38 |
| 507 | 경영·비즈니스 | 2640 | 32 |
| 523 | 마케팅·광고 | 2536 | 23 |
| 511 | 디자인 | 1582 | 27 |
| 510 | 고객서비스·리테일 | 1052 | 24 |
| 530 | 영업 | 854 | 13 |
| 524 | 미디어 | 481 | 18 |
| 513 | 엔지니어링·설계 | 415 | 58 |
| 522 | 제조·생산 | 369 | 14 |
| 508 | 금융 | 313 | 23 |
| 517 | HR | 254 | 15 |
| 10566 | 정보보호 | 170 | 7 |
| 509 | 건설·시설 | 144 | 19 |
| 959 | 게임 제작 | 122 | 9 |
| 532 | 물류·무역 | 103 | 23 |
| 10057 | 식·음료 | 96 | 12 |
| 521 | 법률·법집행기관 | 80 | 13 |
| 10101 | 교육 | 80 | 8 |
| 515 | 의료·제약·바이오 | 65 | 30 |
| 514 | 공공·복지 | 0 | 12 |

## Job category ids (`job_ids`), group 518 개발

> The earlier revision of this table mapped 660, 872, 873, 900, 895 and 677 to
> the wrong names. The values below come straight from the site payload.

| id | Sub-category | Open jobs |
|---|---|---|
| 872 | 서버 개발자 | 911 |
| 10110 | 소프트웨어 엔지니어 | 840 |
| 873 | 웹 개발자 | 721 |
| 669 | 프론트엔드 개발자 | 529 |
| 1634 | 머신러닝 엔지니어 | 498 |
| 674 | DevOps / 시스템 관리자 | 433 |
| 660 | 자바 개발자 | 432 |
| 899 | 파이썬 개발자 | 385 |
| 900 | C,C++ 개발자 | 375 |
| 655 | 데이터 엔지니어 | 374 |
| 895 | Node.js 개발자 | 266 |
| 665 | 시스템,네트워크 관리자 | 220 |
| 1024 | 데이터 사이언티스트 | 203 |
| 877 | 개발 매니저 | 198 |
| 658 | 임베디드 개발자 | 187 |
| 676 | QA,테스트 엔지니어 | 153 |
| 672 | 하드웨어 엔지니어 | 129 |
| 1025 | 빅데이터 엔지니어 | 127 |
| 939 | 웹 퍼블리셔 | 106 |
| 1026 | 기술지원 | 103 |
| 677 | 안드로이드 개발자 | 89 |
| 661 | .NET 개발자 | 86 |
| 893 | PHP 개발자 | 80 |
| 876 | 프로덕트 매니저 | 77 |
| 678 | iOS 개발자 | 67 |
| 10111 | 크로스플랫폼 앱 개발자 | 59 |
| 1027 | 블록체인 플랫폼 엔지니어 | 53 |
| 10231 | DBA | 36 |
| 896 | 영상,음성 엔지니어 | 34 |
| 898 | 그래픽스 엔지니어 | 29 |
| 795 | CTO,Chief Technology Officer | 26 |
| 10230 | ERP전문가 | 24 |
| 894 | 루비온레일즈 개발자 | 22 |
| 1022 | BI 엔지니어 | 9 |
| 10112 | VR 엔지니어 | 7 |
| 10536 | 테크니컬 라이터 | 7 |
| 10531 | RPA 엔지니어 | 4 |
| 793 | CIO,Chief Information Officer | 3 |

## Job category ids for other groups

Read them the same way, or open the group on wanted.co.kr and take `job_ids`
out of the URL:

```bash
curl -s https://www.wanted.co.kr/wdlist \
  | python3 -c "import sys,re,json; d=json.loads(re.search(r'__NEXT_DATA__[^>]*>(.*?)</script>', sys.stdin.read(), re.S).group(1)); \
      [print(g['id'], g['title'], [(t['id'], t['title']) for t in g['tags']]) for g in d['props']['pageProps']['tags']['category']]"
```

The three groups a non-developer job search reaches for most often:

### 523 마케팅·광고

| id | Sub-category | Open jobs |
|---|---|---|
| 710 | 마케터 | 1064 |
| 719 | 마케팅 전략 기획자 | 836 |
| 1635 | 콘텐츠 마케터 | 735 |
| 1030 | 디지털 마케터 | 579 |
| 707 | 브랜드 마케터 | 555 |
| 10138 | 퍼포먼스 마케터 | 504 |
| 950 | 글로벌 마케팅 | 415 |
| 721 | 소셜 마케터 | 367 |
| 763 | 광고 기획자(AE) | 338 |
| 714 | PR 전문가 | 129 |

### 511 디자인

| id | Sub-category | Open jobs |
|---|---|---|
| 592 | 그래픽 디자이너 | 456 |
| 594 | 웹 디자이너 | 384 |
| 599 | UX 디자이너 | 290 |
| 597 | UI,GUI 디자이너 | 277 |
| 603 | 제품 디자이너 | 202 |
| 602 | 영상,모션 디자이너 | 145 |
| 10532 | 콘텐츠 디자이너 | 137 |
| 595 | 모바일 디자이너 | 130 |
| 879 | BI/BX 디자이너 | 127 |
| 952 | 출판, 편집 디자이너 | 127 |

### 507 경영·비즈니스

| id | Sub-category | Open jobs |
|---|---|---|
| 564 | 사업개발·기획자 | 931 |
| 559 | PM·PO | 742 |
| 565 | 서비스 기획자 | 702 |
| 563 | 전략 기획자 | 430 |
| 554 | 운영 매니저 | 257 |
| 1034 | 회계·경리 | 227 |
| 552 | 경영지원 | 184 |
| 562 | 총무 | 166 |
| 656 | 데이터 분석가 | 158 |
| 10232 | 상품기획자(BM) | 155 |
