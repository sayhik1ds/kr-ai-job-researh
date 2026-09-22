import check_facts as C

PROFILE = """
## 성과
- 수집 시간 74% 단축 (크롤링 파이프라인)
- 응답 10.75초 → 2.1초 (원격 dev MySQL, k6)
- 회귀 테스트 질문 107건
- 컨테이너 약 100개 관리
**스택** `Java` `Spring Boot` `PostgreSQL`
- 기간: 2025.04 ~ 현재
"""


def test_subset_passes():
    doc = "- 수집 시간 74% 단축\n- 10.75초 → 2.1초\n`Java` `PostgreSQL`\n2025.04\n"
    assert C.check(PROFILE, doc) == []


def test_changed_number_fails():
    doc = "- 수집 시간 80% 단축\n"
    fails = C.check(PROFILE, doc)
    assert any("80%" in f for f in fails)


def test_changed_unit_fails():
    doc = "- 회귀 테스트 107개 통과\n"
    fails = C.check(PROFILE, doc)
    assert any("107개" in f for f in fails)


def test_unknown_identifier_fails():
    doc = "`Kafka`\n"
    fails = C.check(PROFILE, doc)
    assert any("kafka" in f for f in fails)


def test_allow_list():
    doc = "작성일 2026-09-22\n"
    assert C.check(PROFILE, doc, allow={"2026-09-22", "2026", "09", "22"}) == []


def test_omission_is_fine():
    assert C.check(PROFILE, "- 컨테이너 약 100개 관리\n") == []


def test_noise_ignored():
    doc = "<!-- 999% -->\n```\n555초\n```\nhttps://example.com/123\n[PLACEHOLDER_9]\n"
    assert C.check(PROFILE, doc) == []


def test_backtick_placeholders_do_not_pair_with_real_identifiers():
    assert C.check('`Java`', '`[PLACEHOLDER]` 설명 `Java`') == []


def test_section_and_list_numbers_ignored():
    doc = "#### 1.1 AMAAQ 봇\n1. 첫째\n2. 둘째\n"
    assert C.check(PROFILE, doc) == []


def test_particle_after_unit_not_swallowed():
    prof = "- 질문 6,095건의 로그\n- 107건을 검사\n- 응답 3초를 넘김\n"
    assert C.check(prof, "- 6,095건 처리\n- 107건\n- 3초\n") == []


def test_readme_skipped_by_default(tmp_path):
    p = tmp_path / "p.md"; p.write_text(PROFILE, encoding="utf-8")
    r = tmp_path / "README.md"; r.write_text("총점 77점, 공고 54916782\n", encoding="utf-8")
    assert C.main([str(p), str(r)]) == 0
    assert C.main([str(p), str(r), "--include-readme"]) == 1
