---
framework_version: 0.1.0
---

# 용어 치환표

사내 설계 문서의 어휘를 그대로 옮기지 않는다. 밖에서 읽는 사람에게 뜻이 통하는 말로 바꾼다. `sysbox`, `bind mount`, `DOCKER_HOST` 같은 일반 기술 용어는 그대로 쓴다.

`/setup`이 `documents/`에서 사내 용어를 발견하면 여기에 행을 추가한다. `tools/lint_style.py`가 왼쪽 열을 검사한다.

| 사내 용어 | 대체 |
|---|---|
| [INTERNAL_TERM_1] | [PUBLIC_TERM_1] |
| [INTERNAL_TERM_2] | [PUBLIC_TERM_2] |

## 예시 (형식 참고용)

| 사내 용어 | 대체 |
|---|---|
| 지휘 | 제어 |
| 자기동기화 | 자동 동기화 |
| 위임(서비스 간 호출) | 내부 서비스 호출 |
