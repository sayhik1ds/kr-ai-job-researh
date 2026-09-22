---
name: outcome
description: 지원 결과를 기록하고 제출본을 보관한다. 사용자가 `/outcome` 또는 `$outcome`라고 하면 이 스킬을 쓴다.
disable-model-invocation: true
framework_version: 0.1.0
---

# /outcome [회사_포지션] [상태]

## tracker.csv

헤더:

```
date,portal,job_id,company,position,profile,status,deadline,path,note,attempt,history,snapshot
```

`status` 값: `drafted`, `submitted`, `screening`, `interview_1`, `interview_2`, `offer`, `rejected`, `withdrawn`, `no_response`, `expired`

기록은 `tools/track_application.py`로 갱신한다. 실행 전에 `docs/submission-workflow.md`의 공고별 지원 기록을 읽는다. 기존 CSV의 열은 보존하며, 회차가 없는 행은 첫 회차로 읽는다. 회사명만으로 기록을 선택하지 말고 포털·공고 ID·회차를 확인한다. 여러 건이면 사용자에게 대상만 묻는다.

## 절차

1. 인자가 없으면 `tracker.csv`에서 `submitted` 이후 상태가 바뀌지 않은 지원을 표로 보여주고 어느 것을 갱신할지 묻는다.
2. `python3 tools/track_application.py update --portal <포털> --job-id <공고ID> --attempt <회차> --status <상태> --note <메모>`로 갱신한다. `history`에 이전 상태와 변경 시각도 기록된다.
3. 사용자가 실제 제출했다고 알려주면 `submitted`로 갱신한다. 도구가 해당 시점의 md·pdf·json을 회차별 폴더로 복사하고 `snapshot`에 경로를 기록한다. 제출본은 이후 수정하지 않는다. 같은 상태를 다시 실행해도 복사하지 않는다. 재지원은 `create --new-attempt`로 별도 회차를 만든다.
4. `interview_*`로 바뀌면 `/interview` 실행을 권한다.
5. `rejected`·`offer`면 공고 요건과 격차 목록을 해당 초안 폴더의 `outcome.md`에 적는다. 제출본 폴더는 변경하지 않는다. 몇 건 쌓이면 `04-job-evaluation.md` 가중치 조정에 쓴다.

## /outcome followup

`submitted` 후 14일 지나고 상태 변화가 없는 지원을 보여준다. 후속 연락 문안은 제출본 내용만 근거로 초안을 만든다. 보내지 않는다.
