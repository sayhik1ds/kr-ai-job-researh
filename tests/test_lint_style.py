import os, textwrap
import lint_style as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, ".agents", "skills", "job-application-assistant")


def run(tmp_path, text, gloss=None):
    f = tmp_path / "doc.md"
    f.write_text(textwrap.dedent(text), encoding="utf-8")
    terms = L.load_lint_terms(os.path.join(SKILL, "02-writing-style.md"))
    g = gloss if gloss is not None else []
    return L.lint_file(str(f), terms, g)


def kinds(hits):
    return [(k, m) for _, k, m in hits]


def test_lint_block_loads():
    terms = L.load_lint_terms(os.path.join(SKILL, "02-writing-style.md"))
    assert "자리" in terms and "축" in terms
    assert any(t.startswith("기 때문이") for t in terms)


def test_clean_text_passes(tmp_path):
    hits = run(tmp_path, """
        - 컨테이너 오케스트레이션 도구 구축
        - 배포 자동화 개발. 축소된 범위로 운영
        - **기간** — 2026.03 ~ 2026.06
        | 항목 | 값 — 설명 |
    """)
    assert hits == []


def test_boundary_does_not_hit_inside_word(tmp_path):
    hits = run(tmp_path, "- 인프라 구축과 축소 작업\n")
    assert ("금지 표현", "축") not in kinds(hits)


def test_boundary_hits_with_particle(tmp_path):
    hits = run(tmp_path, "- 두 축을 기준으로 정리\n- 이 문제의 자리는 명확하다\n")
    assert ("금지 표현", "축") in kinds(hits)
    assert ("금지 표현", "자리") in kinds(hits)


def test_because_ending(tmp_path):
    hits = run(tmp_path, "키를 바꾸지 않은 것은 핑퐁이 되기 때문이다.\n")
    assert any(k == "기 때문" for k, _ in kinds(hits))


def test_em_dash_mid_sentence(tmp_path):
    hits = run(tmp_path, "배포 도구 — 사내용 — 를 만들었다.\n")
    assert any(k == "em-dash" for k, _ in kinds(hits))


def test_em_dash_label_bullet_allowed(tmp_path):
    hits = run(tmp_path, "- **역할** — 설계와 구현\n- `DOCKER_HOST` — 원격 소켓\n")
    assert not any(k == "em-dash" for k, _ in kinds(hits))


def test_em_dash_heading_allowed(tmp_path):
    hits = run(tmp_path, "#### 1.1 Kite — 사내 경량 오케스트레이션 도구 (2026.03 ~ 2026.06)\n")
    assert not any(k == "em-dash" for k, _ in kinds(hits))


def test_em_dash_inside_bold_label_and_triangle_bullet(tmp_path):
    hits = run(tmp_path, "▸ **고객사 구축** — NH (2026.05)\n▸ **엔진 (saju — Python)**\n")
    assert not any(k == "em-dash" for k, _ in kinds(hits))


def test_glossary_terms(tmp_path):
    hits = run(tmp_path, "- 컨테이너 지휘 로직 개발\n", gloss=["지휘"])
    assert ("사내 용어", "지휘") in kinds(hits)


def test_glossary_loader_skips_placeholders(tmp_path):
    glossary = tmp_path / "glossary.md"
    glossary.write_text("| 사내 용어 | 대체 |\n|---|---|\n| [INTERNAL_TERM_1] | [EXTERNAL_TERM_1] |\n| 지휘 | 제어 |\n", encoding="utf-8")
    g = L.load_glossary_terms(str(glossary))
    assert not any(t.startswith("[") for t in g)
    assert "지휘" in g


def test_code_fence_and_placeholder_skipped(tmp_path):
    hits = run(tmp_path, """
        [YOUR_HEADLINE]
        <!-- 자리를 잡는다 -->
        ```
        자리를 잡는다. 기 때문이다.
        ```
    """)
    assert hits == []


def test_cli_exit_code(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("조용히 처리했기 때문이다.\n", encoding="utf-8")
    assert L.main([str(f)]) == 1
    assert L.main([str(f), "--warn"]) == 0


def test_digit_prefix_is_unit_not_metaphor(tmp_path):
    hits = run(tmp_path, "- 사람인·점핏·잡코리아가 모두 8자리를 쓴다\n- 3축으로 채점한다\n")
    assert not any(k == "금지 표현" for k, _ in kinds(hits))


def test_bare_metaphor_still_caught(tmp_path):
    hits = run(tmp_path, "- 이 문제의 자리는 명확하다\n")
    assert ("금지 표현", "자리") in kinds(hits)


def test_rule_files_skipped(tmp_path):
    f = tmp_path / "03-glossary.md"
    f.write_text("| 지휘 | 제어 |\n", encoding="utf-8")
    assert L.main([str(f), "--glossary", str(f)]) == 0
    assert L.main([str(f), "--glossary", str(f), "--force"]) == 1
