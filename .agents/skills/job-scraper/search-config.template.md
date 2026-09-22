---
framework_version: 0.1.0
---

# 검색 설정

<!-- /setup --section search 가 채운다. 직접 고쳐도 된다 -->

## 검색어

포털마다 아래 검색어를 순서대로 돌린다.

```queries
[QUERY_1]
[QUERY_2]
```

<!-- 예: 백엔드 개발자 / Spring Boot / AI Agent / LLM -->

## 연차

- [YEARS_MIN] ~ [YEARS_MAX]

## 포털 선택

직군에 맞는 포털만 켠다. 스킬 frontmatter의 `enabled` 를 바꾼다.

| 포털 | 직군 | 기본값 |
|---|---|---|
| 원티드 | 전 직군 | 켬 |
| 사람인 | 전 직군 | 켬 |
| 잡코리아 | 전 직군 | 켬 |
| 그룹바이 | 전 직군. 스타트업 중심 | 켬 |
| 점핏 | **개발 전용** | 개발이 아니면 끈다 |

## 직군 코드 (선택)

코드를 알면 검색어 없이 직군 전체를 훑을 수 있다. 몰라도 된다. 키워드 검색만으로도 전 직군이 동작한다.

- 원티드 job-group: [WANTED_JOB_GROUP] <!-- 518 개발, 523 마케팅·광고, 511 디자인, 507 경영·비즈니스, 530 영업, 517 HR, 508 금융, 510 고객서비스·리테일, 524 미디어. 20개 전체는 wanted-search/url-reference.md -->
- 원티드 job-ids: [WANTED_JOB_IDS] <!-- 개발 하위: 872 서버, 10110 소프트웨어 엔지니어, 873 웹, 669 프론트엔드, 660 자바, 899 파이썬, 655 데이터 엔지니어, 674 DevOps. 직군별 하위 코드는 url-reference.md -->
- 잡코리아 duty-ctgr: [JOBKOREA_DUTY] <!-- 10031 AI·개발·데이터, 10030 마케팅·광고·MD, 10032 디자인, 10035 영업, 10026 기획·전략, 10028 인사·HR, 10029 회계·세무. 전체 목록은 jobkorea-search/url-reference.md -->
- 사람인 cat-kewd: [SARAMIN_CAT] <!-- 직군별 코드 표는 saramin-search/url-reference.md 에 있다. 라벨은 사이트가 보여 준 링크 텍스트라 공식 분류와 다를 수 있다. 카테고리만 쓰면 여러 직군을 한꺼번에 태그한 대량 공고가 상위에 몰리니 검색어와 함께 쓴다 -->

## 제외 패턴 (제목 정규식)

제목만으로 제외할 수 있는 직군. `tools/score_jobs.py`가 `drop` 블록을 읽는다.

```drop
[DROP_PATTERN]
```

<!-- 예: 프론트|front-?end|iOS|안드로이드|QA|시니어|Senior|Lead\b -->

## 키워드 가중치

본문(소개·주요 업무·자격 요건·우대 사항)에 나오면 더하거나 뺀다. 소문자로 비교한다. `tools/score_jobs.py`가 `weights` 블록을 읽는다. 형식은 `키워드 = 정수`.

```weights
# 강점 (양수)
[SKILL_1] = 3
[SKILL_2] = 2
# 불일치 신호 (음수)
[MISMATCH_1] = -3
5년 이상 = -4
```

## 출력 컷

- 표에 보여줄 최소 점수: [MIN_SCORE] <!-- 기본 10 -->
