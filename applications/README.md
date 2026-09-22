# applications/

`/apply`가 작성한 지원 문서 초안을 보관하는 폴더다. 새 문서는 `<포털>_<공고ID>/attempt_<회차>/`에 저장한다. 기존 `<회사>_<포지션>/` 폴더도 사용할 수 있다. md·pdf 파일과 근거 검토 JSON, 제출 요건 JSON을 함께 보관한다. README에는 선택한 프로파일, 수정 사항, 공고 요건과 맞지 않는 부분을 기록한다.

지원 문서는 git 추적에서 제외된다. 제출 후 `/outcome`을 실행하면 `documents/applications/<포털>_<공고ID>/attempt_<회차>/`에 제출본을 복사해 보관한다. 같은 회차의 제출본은 덮어쓰지 않는다. 자세한 사용법은 [지원 문서 검증과 기록](../docs/submission-workflow.md)을 참고한다.
