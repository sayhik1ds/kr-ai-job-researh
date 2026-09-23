import os
import check_codex_skills as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_all_skills_discoverable_by_codex():
    problems, skills = C.check()
    assert not problems, "코덱스 탐색 조건 위반: " + "; ".join(problems)
    assert len(skills) >= 14, f"스킬이 {len(skills)}개뿐이다"


def test_description_budget():
    _, skills = C.check()
    total = sum(s["desc_chars"] for s in skills)
    assert total <= C.LIST_BUDGET, f"description 총합 {total}자가 상한을 넘는다"


def test_workflow_and_portal_skills_present():
    _, skills = C.check()
    names = {s["name"] for s in skills}
    for n in ("setup", "scrape", "rank", "apply", "outcome", "interview"):
        assert n in names, n
    for n in ("wanted-search", "jumpit-search", "groupby-search", "saramin-search", "jobkorea-search"):
        assert n in names, n
    assert "humanize-korean" in names


def test_frontmatter_parser_handles_block_scalars():
    data, err = C.parse_frontmatter("---\nname: x\ndescription: >\n  두 줄로\n  이어진 설명\n---\n본문\n")
    assert err is None
    assert data["name"] == "x"
    assert "이어진 설명" in data["description"]


def test_frontmatter_missing_block():
    data, err = C.parse_frontmatter("# 제목만 있는 파일\n")
    assert data is None and err
