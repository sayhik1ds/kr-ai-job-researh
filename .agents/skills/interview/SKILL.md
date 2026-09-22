---
name: interview
description: 제출본과 공고를 근거로 면접 예상 질문·답변·역질문을 준비한다. 사용자가 `/interview` 또는 `$interview`라고 하면 이 스킬을 쓴다.
disable-model-invocation: true
framework_version: 0.1.0
---

# /interview <회사_포지션> [단계]

`07-interview-prep.md` 형식을 따른다.

1. `tracker.csv`에서 포털·공고 ID·회차를 확인하고 `snapshot`에 기록된 제출본과 공고 원문을 읽는다. 기존 기록에 snapshot이 없으면 `documents/applications/<회사>_<포지션>/`에서 찾는다. 제출본이 없으면 `applications/`의 초안을 쓰되 "제출본 아님"을 표시한다.
2. 공고 요건과 제출본을 대조해 충족·격차 표를 만든다.
3. 예상 질문 10개. 질문마다 근거 문장, 구술 답변, 근거(케이스·PR), 꼬리 질문.
4. 격차 질문. 인정하고 인접 경험을 말하는 답변.
5. 역질문 5개. 회사 공식 사이트에서 확인한 사실에 기반.
6. 새 자료는 `interview/<포털>_<공고ID>_attempt_<회차>.md`에 저장한다. 과거 회사별 파일은 그대로 둔다.
7. 사용자가 원하면 모의 면접. 한 번에 질문 하나, 답변 후 피드백.

## 금지

- 제출본에 없는 경험을 답변에 넣지 않는다
- 확인 안 된 회사 정보를 역질문에 쓰지 않는다
