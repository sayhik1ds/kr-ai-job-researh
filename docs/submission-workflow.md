# 지원 문서 검증과 기록

`/apply`는 문서를 작성한 뒤 수치 검사, 근거 검토, 제출 요건 검사, PDF 확인을 거친다. 개인별 검사 파일은 지원 문서와 같은 `applications/` 폴더에 저장한다.

## 문장별 근거 검토

`check_facts.py`는 프로필 전체에 수치와 코드 식별자가 있는지 확인한다. 이 검사만으로는 프로젝트가 바뀌거나 역할이 과장된 것을 판단하지 못한다.

문서마다 `이력서.evidence.json`처럼 근거 파일을 만든다. 작성 에이전트가 각 본문 문장과 프로필 원문을 연결하고, 독립 리뷰 에이전트가 프로젝트, 개인 역할, 팀 성과, 측정 조건을 대조한다. 검토가 끝난 최종 문서를 기준으로 해시를 기록한다. 해시는 `hashlib.sha256(text.encode('utf-8')).hexdigest()`로 계산한다. 텍스트는 `Path.read_text()`로 읽는다.

```json
{
  "profile_sha256": "[PROFILE_HASH]",
  "document_sha256": "[DOCUMENT_HASH]",
  "reviewer": "[REVIEW_AGENT_ID]",
  "claims": [
    {
      "id": "[FACT_ID]",
      "claim": "[EXACT_DOCUMENT_TEXT]",
      "source_quote": "[EXACT_PROFILE_TEXT]",
      "document_context": ["[DOCUMENT_HEADING]", "[PROJECT_HEADING]"],
      "source_context": ["[PROFILE_HEADING]", "[PROJECT_HEADING]"],
      "review": {
        "status": "supported",
        "reason": "[REVIEW_REASON]"
      }
    }
  ]
}
```

- `id`는 해당 문서에서 고유한 근거 ID다. 같은 주장을 수정할 때는 기존 ID를 유지한다.
- `claim`과 `source_quote`는 각각 주석을 제외한 문서와 프로필에서 한 곳에만 존재하는 원문이다. 반복 문장이면 앞뒤 문장을 포함해 구분한다.
- `document_context`와 `source_context`는 각 인용문이 속한 제목 계층이다. 제목의 번호도 포함한다. `check_evidence.context_at()`으로 얻을 수 있다.
- 제목과 구분선을 제외한 본문 전체를 연결한다. 연락처와 역량 목록도 포함한다. 여러 원문이 필요한 문단은 주장별로 나눠 연결한다.
- 독립 리뷰는 제목에 적힌 회사와 프로젝트까지 확인한다. 근거가 맞지 않으면 `unsupported`로 기록하고 문서를 고친 뒤 다시 검토한다. 도구는 자연어 의미나 리뷰 에이전트의 신원을 자동 판별하지 않는다.
- 문서나 프로필을 수정하면 해시가 달라져 검사가 실패한다. 해시만 갱신하지 말고 변경된 주장과 맥락을 다시 검토한다.

```bash
python3 tools/check_facts.py <profile.md> <document.md>
python3 tools/check_evidence.py <profile.md> <document.md> <document.evidence.json>
```

## 제출 요건 검사

공고에 명시된 문항과 분량, 프로필의 연락처로 `submission.json`을 만든다. 다른 회사명이 남아 있는지 검사할 때는 이전 지원 대상 회사명을 `forbidden`에 넣는다. 실제 경력에 포함된 회사는 금지 목록에 넣지 않는다.

```json
{
  "documents": [
    {
      "path": "이력서.md",
      "required": ["[YOUR_NAME]", "[YOUR_EMAIL]"],
      "forbidden": []
    },
    {
      "path": "자기소개서.md",
      "required": [],
      "forbidden": ["[PREVIOUS_APPLICATION_COMPANY]"],
      "sections": [
        {
          "heading": "1. 지원 동기",
          "min": 1,
          "max": 800,
          "count": "with_spaces"
        }
      ]
    }
  ]
}
```

예시의 placeholder는 실제 값으로 바꾼다. 제출할 문서만 목록에 넣고, 공고에 없는 제한은 만들지 않는다. 문항 제목은 마크다운의 제목과 정확히 일치해야 한다. 글자 수는 제목과 마크다운 장식을 제외한 답변을 센다. `with_spaces`는 내부 공백과 줄바꿈을 포함하고 `without_spaces`는 공백 문자를 제외한다. 채용 사이트의 계산 방식이 다르면 해당 입력창에서도 확인한다.

```bash
python3 tools/check_submission.py applications/<지원폴더>/submission.json
python3 tools/verify_pdf.py <이력서.pdf> --max-pages 2 --expect <이름> <이메일> --render-dir _workspace/<고유한검토폴더>
```

PDF 이미지 생성에는 Poppler의 `pdftoppm`이 필요하다. 모든 페이지 이미지를 열어 잘림, 겹침, 빈 페이지를 확인한다. 이미지 생성이나 텍스트 검사 통과만으로 시각 검토가 끝난 것은 아니다. 렌더러가 없으면 검사 상태를 미완료로 남긴다. 다른 PDF에도 별도 검토 폴더를 사용한다.

## 공고별 지원 기록

새 초안은 `applications/<포털>_<공고ID>/attempt_<회차>/`에 만든다. 과거의 `<회사>_<포지션>/` 폴더도 그대로 사용할 수 있다. 포털이 없는 공고는 `manual`과 중복되지 않는 ID를 사용한다.

```bash
python3 tools/track_application.py create --portal wanted --job-id 123 --company 회사 --position 직무 --path applications/wanted_123/attempt_1
python3 tools/track_application.py update --portal wanted --job-id 123 --attempt 1 --status submitted
python3 tools/track_application.py list
```

`create`는 같은 공고가 있으면 중단한다. 실제 재지원할 때만 `--new-attempt`를 붙이고 새 초안 경로를 지정한다. `update`는 항상 회차를 받는다. 공고 ID는 문자열로 처리한다.

`submitted`로 처음 바뀌면 md·pdf·json 파일을 `documents/applications/<포털>_<공고ID>/attempt_<회차>/`에 복사하고 파일별 SHA-256을 남긴다. 기존 제출 폴더는 덮어쓰지 않는다. 도구는 사용자가 실제 제출했다고 알려준 뒤 실행한다. 제출 전에 검증 도구를 실행하며, 상태 기록 도구 자체가 문서 품질을 판정하지는 않는다.

기존 `tracker.csv`의 열과 값은 보존한다. `attempt`, `history`, `snapshot` 열을 추가하며, 회차가 없는 기존 행은 첫 회차로 읽는다. 같은 포털·공고 ID·회차가 중복된 기록은 자동으로 합치지 않는다. 이력은 `history` 열의 JSON에 기록한다. 기존 제출 상태를 다시 기록해도 현재 초안을 과거 제출본으로 복사하지 않는다.

후속 결과와 면접 자료는 제출본 폴더 밖에 둔다. `/interview`는 `snapshot` 경로를 우선 사용하고, 과거 기록은 기존 제출 폴더에서 찾는다. 자동 후속 연락은 보내지 않는다.
