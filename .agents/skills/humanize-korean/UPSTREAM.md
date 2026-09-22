# 출처

이 디렉토리는 [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai)의 `codex/skills/humanize-korean/`을 그대로 복사한 것이다. MIT 라이선스, Copyright (c) 2026 epoko77-ai.

| 항목 | 값 |
|---|---|
| 업스트림 커밋 | `14aeb52d13e737beb4e999cb7cb92275d0969689` |
| 업스트림 날짜 | 2026-06-09 |
| 플러그인 버전 | 1.5.0 |
| 복사한 날 | 2026-09-22 |

여기 있는 `SKILL.md`와 `references/`는 수정하지 않는다. `SKILL.md`가 참조하는 `references/` 4개(quick-rules, rewriting-playbook, ai-tell-taxonomy, scholarship)만 가져왔고 메트릭 스크립트·baseline·웹 명세는 뺐다. 갱신은 `bash tools/update_humanizer.sh`로 한다. 우리 쪽 적용 규칙(어느 문서에 걸고 어느 문서는 제외하는지)은 `apply` 스킬에 있다.

이 복사본은 Fast 모드(단일 호출)만 담고 있다. 5개 에이전트가 도는 strict 모드는 원본 저장소를 Claude Code 플러그인으로 설치하면 쓸 수 있다.
