# ai-job-search-kr

저장소: [sayhik1ds/kr-ai-job-researh](https://github.com/sayhik1ds/kr-ai-job-researh)

한국 채용 시장에 맞춘 AI 구직 도구다. [Claude Code](https://claude.com/claude-code)와 [Codex CLI](https://developers.openai.com/codex)에서 쓴다. 저장소를 내려받아 프로필을 채우면 AI가 공고 수집부터 적합도 평가, 이력서·포트폴리오·자기소개서 작성, 면접 준비까지 돕는다.

[MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)의 설계를 한국 시장에 맞게 바꿨다. 주요 차이는 다음과 같다.

| | ai-job-search | ai-job-search-kr |
|---|---|---|
| 포털 | Jobindex·Jobnet 등 덴마크 | 원티드·점핏·그룹바이·사람인·잡코리아 |
| 작성 문서 | LaTeX CV 2쪽 + 커버레터 1쪽 | 마크다운 이력서·포트폴리오·자기소개서 문항 답변 |
| PDF | lualatex·xelatex | pandoc + Chrome 헤드리스 |
| 평가 기준 | 언어 게이트·통근·연봉 | 연차 요구·필수/우대 요건·근무지·직무 유형 |
| 문체 규칙 | 영어 | 한국어 개조식. 은유·문장 중간 부연·`~기 때문` 종결 금지 |
| AI 문체 제거 | 없음 | humanize-korean 내장. 자기소개서·포트폴리오 서술부에 적용 |
| 프로필 구성 | 공고마다 새로 작성 | 직무 유형별 프로파일을 정해 조합 |
| 직군 | 지원자 분야 그대로 | 직군을 받아 역량 칸·태그·포트폴리오 구성을 맞춘다 |

## 처음 쓰는 사람을 위한 안내

개발 경험이 없어도 아래 순서대로 시작할 수 있다. 맥에서는 "터미널", 윈도우에서는 "PowerShell"을 열고 명령어를 한 줄씩 입력한다.

1. **저장소 내려받기**
   ```bash
   git clone https://github.com/sayhik1ds/kr-ai-job-researh.git
   cd kr-ai-job-researh
   ```
   git이 없으면 [공식 사이트](https://git-scm.com)에서 설치한다. [저장소 페이지](https://github.com/sayhik1ds/kr-ai-job-researh)의 "Code → Download ZIP"으로 내려받은 뒤 압축을 풀고 그 폴더로 이동해도 된다.

2. **필요한 프로그램 설치하기** 아래 스크립트가 설치 여부를 확인하고 빠진 프로그램을 설치한다.

   맥과 리눅스는 터미널에서
   ```bash
   bash install.sh
   ```
   윈도우는 PowerShell에서
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```
   마지막에 `정상 N, 없음 0`이 나오면 준비가 끝난다. `[없음]`이 남아 있으면 함께 표시된 안내에 따라 설치한 뒤 다시 실행한다. 설치 상태만 확인하려면 뒤에 `--check`를 붙인다. 윈도우는 `-Check`다.

3. **AI 도구 선택하기** [Claude Code](https://claude.com/claude-code)와 [Codex CLI](https://developers.openai.com/codex) 중 하나를 설치한다. 저장소 폴더에서 `claude` 또는 `codex`를 입력하면 대화창이 열린다.

   터미널 화면이 불편하면 **데스크톱 앱**을 사용해도 된다. Claude Code는 맥·윈도우용 앱이 있고, Codex는 `codex app`으로 앱을 연다. 앱에서 저장소 폴더를 열면 채팅창에 같은 명령을 입력하고 만들어진 파일도 확인할 수 있다. 2단계의 설치 스크립트는 터미널에서 한 번 실행해야 한다.

4. **기존 자료 넣기** 이력서 파일을 `documents/resume/` 폴더에 복사한다. PDF, 워드에서 저장한 마크다운, 텍스트 파일을 사용할 수 있다. 포트폴리오가 있으면 `documents/portfolio/`에 넣는다. 자료가 없어도 다음 단계에서 AI의 질문에 답하며 진행할 수 있다.

5. **대화창에서 작업 시작하기** 아래 명령을 순서대로 입력한다. Claude Code에서는 `/이름`, Codex에서는 `$이름` 형식을 쓴다.

   | 입력 | 하는 일 |
   |---|---|
   | `/setup` | 이력서를 읽고 프로필을 만든다. 부족한 정보는 질문으로 확인한다 |
   | `/scrape` | 원티드·점핏·그룹바이·사람인·잡코리아에서 공고를 모은다 |
   | `/rank` | 모은 공고를 내 프로필 기준으로 채점해 순위를 매긴다 |
   | `/apply <공고 주소>` | 공고 주소를 붙여넣으면 이력서·포트폴리오·자기소개서를 작성하고 PDF로 저장한다. 어색한 AI 문체도 다듬는다 |
   | `/outcome` | 지원 결과를 기록한다 |
   | `/interview 회사_포지션` | 면접 예상 질문과 답변을 준비한다 |

   새 문서는 `applications/<포털>_<공고ID>/attempt_<회차>/`에 저장된다. 기존 회사별 폴더도 계속 사용할 수 있다.

**작성 원칙.** 이력서에 없는 경험이나 기술을 공고에 맞추려고 추가하지 않는다. 공고 요건과 맞지 않는 부분은 따로 알려준다.

**개인정보 관리.** `documents/`, `applications/`, `interview/`, 수집한 공고, 지원 기록표, `/setup`이 채우는 프로필·검색 설정 파일은 git 추적에서 제외된다. 저장소에는 `[PLACEHOLDER]`가 들어 있는 `*.template.md`를 둔다. 설치 스크립트가 이 템플릿을 복사해 실제로 쓸 파일을 만든다. 공개 저장소에 올리기 전에는 `git status`로 개인 자료가 섞이지 않았는지 확인한다.

---

## 사용법

명령 6개를 순서대로 쓴다. Claude Code에서는 `/이름`, Codex에서는 `$이름`이다. 각 명령은 앞 단계가 만든 파일을 읽으므로 순서를 지킨다. 아래 소요 시간과 출력 예시는 2026년 9월 22일 실제 실행 기준이다.

### 1. `/setup` — 프로필 만들기

`documents/` 폴더의 자료를 읽어 경력, 프로젝트, 수치, 역량을 구조화한 프로필로 옮긴다. 처음 한 번만 실행하면 된다.

먼저 직군을 확인한다. 이력서를 읽고 "퍼포먼스 마케팅으로 보고 진행한다"처럼 제안하면 맞는지 답하면 된다. 직군에 따라 역량 칸 이름과 포트폴리오 구성이 달라진다. 개발자는 언어와 프레임워크, 마케터는 채널과 지표, 디자이너는 도구와 산출물이 들어간다. 목록에서 고르는 방식이 아니라서 직군 이름은 자유롭게 적으면 된다.

```
/setup
```

읽는 자료는 다음과 같다. 없는 폴더는 건너뛴다.

| 폴더 | 넣을 것 |
|---|---|
| `documents/resume/` | 지금 쓰는 이력서. PDF, 마크다운, 텍스트 |
| `documents/portfolio/` | 포트폴리오 |
| `documents/cover_letters/` | 과거 자기소개서 |
| `documents/notes/` | 경력 기간, 연락처, 사내 용어 치환 메모 등 자유 형식 |

만들어지는 파일은 4개다. 모두 git 추적에서 제외된다.

- `01-candidate-profile.md` 경력과 프로젝트. 이후 모든 문서가 이 파일만 사실 출처로 쓴다
- `03-glossary.md` 사내 용어를 외부에서 통하는 말로 바꾸는 표
- `05-profiles.md` 직무 유형별로 어떤 프로젝트를 어떤 순서로 넣을지 정한 프로파일
- `search-config.md` 공고 검색어와 키워드 가중치

프로젝트마다 태그(`ai`, `backend`, `devops`, `integration`, `payment`, `data`, `infra`)가 붙는다. 프로파일이 이 태그로 항목을 고른다. 자료에 없는 정보는 추정하지 않고 질문으로 확인한다. 실행에 20~30분 걸린다.

검색어만 다시 만들려면 `/setup --section search`를 쓴다.

### 2. `/scrape` — 공고 모으기

포털 5곳에서 공고를 받아 중복을 지우고 1차 채점한다.

```
/scrape
/scrape "AI Agent"        # 검색어를 직접 지정
```

포털별로 다음과 같이 받는다. 잡코리아는 robots.txt가 키워드 검색을 막아 직군 목록을 받은 뒤 제목으로 거른다.

| 포털 | 방식 | 직군 |
|---|---|---|
| 원티드 | 검색어. 직군 코드를 알면 훑기도 | 전 직군 |
| 사람인 | 검색어 + 경력·지역 필터 | 전 직군 |
| 잡코리아 | 직군·지역·연차 목록 + 제목 필터 | 전 직군 |
| 그룹바이 | 최신 10건 | 전 직군. 스타트업 중심 |
| 점핏 | 검색어 | 개발 전용. 다른 직군이면 꺼진다 |

실행 결과는 다음과 같았다.

```
합침 540건 (중복 162, 이미 본 것·북마크 0) → job_scraper/jobs_2026-09-22.json
포털별: groupby 10, jobkorea 193, jumpit 33, saramin 201, wanted 103
```

상위 60건은 본문까지 받아 다시 채점한다. 제목만 보면 국비지원 교육 광고가 상위에 섞인다. 수집에 3~5분 걸린다.

### 3. `/rank` — 순위 매기기

상위 공고의 본문을 읽고 프로필과 대조해 점수를 매긴다. 1차 채점이 키워드만 세는 것과 달리 요건을 하나씩 본다.

```
/rank
/rank 10        # 상위 10건을 평가. 기본 7건
```

먼저 게이트로 거른다. 연차가 프로필보다 2년 이상 많으면 탈락 후보, 1년 이내면 확인 대상이다. 근무지와 필수 요건도 본다. 통과한 공고는 요건 일치, 경험 일치, 직무 유형 적합으로 채점한다.

출력은 이런 표다.

```
| # | 총점 | 판정 | 회사 | 포지션 | 연차 | 마감 |
|---|---|---|---|---|---|---|
| 1 | 87 | 지원 권장 | (주)스카우트 | AI Agent / LLM 기반 개발 | 3~10년 | 채용시 |
| 2 | 84 | 지원 권장 | 디딤(주) | AI Agent / LLM 기반 개발자 | 3~6년 | 2026-10-10 |
| 3 | 77 | 지원 권장 | (주)뉴데이소프트 | AI Agent / LLM Engineer | 신입/경력 5년 이하 | 2026-09-30 |

게이트 탈락 후보: ㈜인텔리콘연구소 (4년 이상 요구)
```

공고마다 강점과 격차가 함께 나온다. 격차는 지원 문서에 절대 반영하지 않는다. 건당 1~2분 걸린다. 여러 건을 동시에 평가한다.

### 4. `/apply` — 지원 문서 만들기

공고 하나를 골라 문서를 만든다. 순위표의 번호, 공고 id, 주소 중 아무거나 쓴다.

```
/apply https://www.wanted.co.kr/wd/379643
/apply https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=54916782
/apply 3                    # /rank 직후라면 순위표 번호
/apply saramin 54916782     # 포털 이름 + 공고 번호
```

주소를 쓰는 편이 확실하다. 번호만 쓰면 어느 포털인지 알 수 없다. 사람인, 점핏, 잡코리아가 모두 8자리 번호를 쓴다.

포털이 접근을 막는 공고는 본문을 그대로 붙여넣어도 된다.

진행 순서는 8단계다.

1. 공고를 평가한다. `/rank`를 이미 돌렸으면 그 결과를 쓴다
2. 직무 유형 프로파일을 고른다. 항목 순서와 강조가 정해진다
3. 이력서와 포트폴리오를 쓴다. 자기소개서는 공고가 요구할 때만 만든다
4. 리뷰 에이전트가 따로 검토한다. 프로필에 없는 주장, 요건 누락, 문체 위반을 찾는다
5. 문체 검사를 돌린다
6. AI 문체를 다듬는다. 이력서, 포트폴리오, 자기소개서의 문장형 산문이 대상이다. 명사형으로 끝나는 불릿과 수치 행은 그대로 둔다
7. 수치와 고유명사가 프로필과 같은지 대조하고 PDF를 만든다
8. 문장별 근거와 제출 요건을 검사하고 PDF 페이지를 확인한다. 지원 회차를 기록하고 확인 목록을 낸다

새 결과물은 공고 ID와 지원 회차별 폴더에 들어간다. 기존 회사별 폴더도 사용할 수 있다.

```
applications/<포털>_<공고ID>/attempt_<회차>/
├── 이력서.md · 이력서.pdf          # 2쪽
├── 포트폴리오.md · 포트폴리오.pdf   # 케이스마다 새 페이지
├── 이력서.evidence.json           # 문장별 근거와 검토 기록. 문서마다 작성
├── submission.json               # 제출 문항·연락처·분량 검사 설정
└── README.md                      # 프로파일, 항목 순서, 뺀 것, 격차
```

같이 나오는 `README.md`에 무엇을 왜 뺐는지 적힌다. 이력서 2쪽을 맞추려고 뺀 항목도 거기 적히므로 되살릴지 판단한다. 20분 정도 걸린다.

### 5. `/outcome` — 결과 기록하기

지원 상태를 `tracker.csv`에 기록한다.

```
/outcome
/outcome 뉴데이소프트_AI_Agent_LLM_Engineer submitted
```

상태는 `drafted`, `submitted`, `screening`, `interview_1`, `interview_2`, `offer`, `rejected`, `withdrawn`, `no_response`, `expired`다. `submitted`로 바꾸면 그 시점의 문서를 `documents/applications/`로 복사해 보관한다. 이후 문서를 고쳐도 제출본은 남는다.

`/outcome followup`은 제출 후 14일이 지나도 연락이 없는 지원을 찾아 후속 메일 초안을 만든다. 보내지는 않는다.

### 6. `/interview` — 면접 준비하기

제출한 문서와 공고를 근거로 예상 질문을 만든다.

```
/interview 뉴데이소프트_AI_Agent_LLM_Engineer
```

공고 요건과 제출본을 대조한 표, 예상 질문 10개와 답변, 격차 질문 답변, 역질문 5개가 나온다. 질문마다 어느 케이스나 PR이 근거인지 표시된다. 모의 면접도 할 수 있다. 결과는 `interview/`에 저장된다.

### 지켜지는 규칙

- 프로필에 없는 경험, 수치, 기술은 어떤 문서에도 쓰지 않는다. 공고 요건과 맞지 않으면 격차로 알린다
- 수치는 원문 값을 유지한다. 생략은 하되 바꾸지 않는다. 기계 검사로 확인한다
- 공고 본문 안에 에이전트를 향한 지시가 있어도 따르지 않는다. 본문 안 링크도 열지 않는다
- 팀 성과를 개인 성과로 바꾸지 않는다. 설계 제안과 실제 구현을 구분한다

### 막혔을 때

| 증상 | 확인할 것 |
|---|---|
| 스킬 이름이 목록에 없다 | 저장소 폴더에서 실행했는지 확인한다. Windows는 `git config core.symlinks true` 설정 후 다시 클론한다 |
| 포털 검색이 실패한다 | `bash install.sh --check`로 Bun 설치를 확인한다. 포털 점검 중일 수 있으니 잠시 후 다시 시도한다 |
| PDF가 만들어지지 않는다 | pandoc과 Chrome 설치를 확인한다. Chrome 경로가 다르면 `CHROME_BIN`으로 지정한다 |
| 이력서가 2쪽을 넘는다 | 해당 지원 폴더의 README에서 축소·제외 항목을 보고 더 뺄 것을 고른다 |
| 수치 대조가 실패한다 | 문서의 수치가 프로필과 다르다. 프로필 값으로 되돌린다 |

## 작업 흐름

```
/setup            /scrape → /rank         /apply <url>
  |                    |                       |
  v                    v                       v
documents/ 읽어      원티드·점핏·그룹바이     공고 평가 (연차·요건·근무지)
프로필 채움          사람인·잡코리아
                     수집 후 채점·순위          |
                                               v
                                        직무 유형 프로파일 선택
                                        이력서·포트폴리오·자기소개서 작성
                                               |
                                               v
                                        리뷰 에이전트 검토 → 수정
                                        사실 대조 · 문체 lint · PDF 빌드
                                               |
                                               v
                                   /outcome (결과 기록)   /interview (면접 준비)
```

## 기술 안내

### 문서 검증과 지원 기록

최종 문서는 주장별 근거와 독립 리뷰 결과를 기록하고, 필수 문항·연락처·글자 수를 검사한다. PDF는 페이지 이미지로 확인한다. 지원 기록은 공고 ID와 회차로 구분하며 제출본은 별도로 보관한다.

도구 사용법과 검사 파일 형식은 [지원 문서 검증과 기록](docs/submission-workflow.md)에 정리했다. 숫자 검사만으로 역할이나 성과의 정확성을 판단하지 않으며, 의미 검토는 독립 리뷰 에이전트가 맡는다.

### 준비물

`install.sh`는 아래 프로그램을 확인하고 설치한다. 직접 설치해도 된다.

- Python 3.10 이상. `.venv`에 pypdf, pytest를 설치한다
- [Bun](https://bun.sh). 포털 검색 CLI를 실행할 때 사용한다
- pandoc, Google Chrome. PDF 생성에 사용한다. Chrome 경로가 다르면 `CHROME_BIN`으로 지정한다
- Claude Code 또는 Codex CLI

### Claude Code와 Codex의 스킬 공유 방식

스킬 원본은 `.agents/skills/`에 모여 있다. Codex는 이 디렉토리를 직접 읽으며 `$이름`으로 스킬을 실행한다. Claude Code가 읽는 `.claude/skills/<이름>`은 `.agents/skills/<이름>`을 가리키는 심볼릭 링크다. Windows에서 클론하면 `git config core.symlinks true`가 필요하다. 설정 없이 받았거나 ZIP으로 내려받아 링크가 깨졌다면 설치 스크립트가 다시 만든다. 윈도우에서는 관리자 권한이 필요 없는 디렉토리 정션을 쓴다.

Codex에는 인자 치환 기능이 없어 스킬 본문에 "스킬 이름 뒤에 적은 문자열"을 인자로 읽도록 안내했다.

2026년 9월 23일 Codex CLI 0.155.1에서 `/skills`로 스킬 14개가 모두 표시되는 것을 확인했다. `python3 tools/check_codex_skills.py`가 같은 조건을 정적으로 검사하므로 스킬을 고친 뒤에는 이 명령으로 확인하면 된다.

## 파일 구조

```
kr-ai-job-researh/
├── install.sh                     # 의존성 확인·설치 (맥·리눅스). --check 는 상태만
├── install.ps1                    # 같은 일을 하는 윈도우용. 깨진 스킬 링크를 정션으로 복구
├── CLAUDE.md                      # 클로드 코드용 규칙 요약
├── AGENTS.md                      # 코덱스 등 다른 에이전트용 규칙 요약
├── .agents/skills/                # 스킬 원천. 클로드 코드·코덱스가 같은 파일을 읽는다
│   ├── setup/ scrape/ rank/ apply/ outcome/ interview/   # 워크플로 스킬 (SKILL.md 하나씩)
│   ├── job-application-assistant/
│   │   ├── SKILL.md
│   │   ├── 01-candidate-profile.md   # 사실 저장소. 경력·프로젝트·수치·근거 (gitignore. *.template.md 가 원본)
│   │   ├── 02-writing-style.md       # 한국어 문체 규칙
│   │   ├── 03-glossary.md            # 사내 용어 → 외부 표현 치환표
│   │   ├── 04-job-evaluation.md      # 공고 평가 기준
│   │   ├── 05-profiles.md            # 직무 유형별 프로파일 (항목 순서·강조)
│   │   ├── 06-document-templates.md  # 이력서·포트폴리오·자기소개서 구조
│   │   └── 07-interview-prep.md      # 면접 준비 형식
│   ├── job-scraper/
│   │   ├── SKILL.md
│   │   └── search-config.md          # 검색어·직군 필터·제외 패턴
│   ├── humanize-korean/           # 한글 AI 문체 제거 (epoko77-ai/im-not-ai 복사본, UPSTREAM.md 참고)
│   ├── wanted-search/             # 포털 검색 CLI (Bun)
│   ├── jumpit-search/
│   ├── groupby-search/
│   ├── saramin-search/            # 검색·상세. robots.txt 허용 경로만 사용
│   └── jobkorea-search/           # 직군·지역·연차 목록 + 상세. 키워드는 클라이언트 필터
├── .claude/
│   ├── skills/<이름> → ../../.agents/skills/<이름>   # 심볼릭 링크 14개
│   └── settings.json
├── templates/                     # 이력서·포트폴리오·자기소개서 마크다운 골격 + CSS
├── tools/
│   ├── check_codex_skills.py      # 코덱스가 스킬 14개를 읽을 수 있는지 검사
│   ├── humanize_split.py          # 산문만 뽑아 휴머나이저에 넘기고 제자리로 복원
│   ├── merge_jobs.py              # 포털 5종 출력을 한 스키마로 합치고 중복 제거
│   ├── score_jobs.py              # 키워드 가중치 채점
│   ├── enrich_jobs.py             # 상위 공고 본문 수집
│   ├── rank_table.py              # 평가 결과를 순위표로
│   ├── wanted_bookmarks.py        # 원티드 북마크 수집 (쿠키 필요)
│   ├── lint_style.py              # 문체 규칙·용어 검사
│   ├── check_facts.py             # 수치·고유명사 보존 대조
│   ├── check_evidence.py          # 문장별 근거·검토 기록·변경 여부 검사
│   ├── check_submission.py        # 필수 문구·미완성 표기·문항 분량 검사
│   ├── track_application.py       # 지원 회차·상태 이력·제출본 보관
│   ├── verify_pdf.py              # PDF 쪽수·텍스트 검사
│   ├── build_pdf.py               # pandoc + Chrome. 맥·리눅스·윈도우 공용
│   ├── build_pdf.sh               # build_pdf.py 로 넘기는 래퍼
│   └── update_humanizer.sh        # 휴머나이저 스킬을 업스트림에서 다시 복사
├── tests/
├── documents/                     # 원본 자료 (gitignore)
├── applications/                  # 생성 문서 (gitignore)
├── interview/                     # 면접 자료 (gitignore)
├── job_scraper/                   # 수집 결과 (gitignore)
└── tracker.csv                    # 지원 기록표 (gitignore)
```

## 검사

```bash
.venv/bin/python -m pytest -q
python3 tools/check_codex_skills.py   # 코덱스 스킬 탐색 조건
for s in wanted-search jumpit-search groupby-search saramin-search jobkorea-search; do (cd .agents/skills/$s/cli && bun run typecheck); done
```

## 라이선스

MIT. 원티드·점핏·그룹바이 스킬은 ai-job-search에서 가져왔고 같은 라이선스로 배포한다. 사람인·잡코리아 스킬은 이 저장소에서 작성했다. `humanize-korean` 스킬은 [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai)(MIT)의 Fast 모드 복사본이다. 정밀 strict 모드가 필요하면 원본을 Claude Code 플러그인으로 설치한다.
