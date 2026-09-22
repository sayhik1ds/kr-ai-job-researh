# documents/

`/setup`이 읽을 이력서와 포트폴리오 등 원본 자료를 보관하는 폴더다. README와 `.gitkeep`만 git으로 관리하고, 개인 자료는 추적에서 제외한다.

```
documents/
├── resume/          # 기존 이력서 (md·pdf)
├── portfolio/       # 기존 포트폴리오
├── cover_letters/   # 과거 자기소개서
├── postings/        # 공고 원문 (/apply가 저장. 접근이 막힌 공고는 직접 붙여넣기)
└── applications/    # 제출본 보관 (/outcome이 복사)
    └── <포털>_<공고ID>/attempt_<회차>/
        ├── 이력서.md · 이력서.pdf
        ├── 포트폴리오.md · 포트폴리오.pdf
        ├── 자기소개서.md (있으면)
        ├── posting.md   # 공고 원문
        └── _submission_manifest.json   # 제출 시각과 파일별 해시
```

경력과 프로젝트가 가장 자세히 정리된 이력서를 `resume/`에 넣는다. 회사별 지원 문서는 `/apply`가 이 자료를 바탕으로 작성한다.

기존 `<회사>_<포지션>/` 제출 폴더는 유지한다. 제출 이후의 결과 메모는 초안 폴더에 기록하며 보관된 제출본은 수정하지 않는다.
