"""추적되는 규칙 파일에 개인 데이터가 들어가지 않았는지 검사한다.

/setup 이 채우는 실제 파일(01-candidate-profile.md 등)은 gitignore 대상이고,
placeholder 원본은 *.template.md 로 추적한다. 이 테스트는 템플릿과 추적 파일만 본다.
"""
import os, re, pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, ".agents", "skills", "job-application-assistant")
SCRAPER = os.path.join(ROOT, ".agents", "skills", "job-scraper")

MUST_HAVE = {
    os.path.join(SKILL, "01-candidate-profile.template.md"): ["[YOUR_NAME]", "[YOUR_EMAIL]", "[YOUR_FIELD]", "[SKILL_LABEL_1]"],
    os.path.join(SKILL, "03-glossary.template.md"): ["[INTERNAL_TERM_1]"],
    os.path.join(SKILL, "05-profiles.template.md"): ["[PROFILE_1_NAME]"],
    os.path.join(SCRAPER, "search-config.template.md"): ["[QUERY_1]", "[DROP_PATTERN]"],
    os.path.join(ROOT, "templates", "resume.md"): ["[YOUR_NAME]", "[YOUR_FIELD]", "[SKILL_LABEL_1]"],
    os.path.join(ROOT, "templates", "portfolio.md"): ["[SKILL_LABEL_1]"],
}
PERSONAL = {"01-candidate-profile.md", "03-glossary.md", "05-profiles.md", "search-config.md"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


@pytest.mark.parametrize("path,tokens", list(MUST_HAVE.items()))
def test_placeholders_present(path, tokens):
    s = open(path, encoding="utf-8").read()
    for t in tokens:
        assert t in s, f"{os.path.relpath(path, ROOT)} 에 {t} 없음. 개인 데이터가 들어갔는지 확인"


def test_no_real_email_in_tracked_rule_files():
    for d in (SKILL, SCRAPER, os.path.join(ROOT, "templates"), os.path.join(ROOT, ".agents", "skills", "apply")):
        for fn in os.listdir(d):
            if not fn.endswith(".md") or fn in PERSONAL:
                continue
            s = open(os.path.join(d, fn), encoding="utf-8").read()
            assert not EMAIL.search(s), f"{fn} 에 이메일 주소가 있다"


def test_personal_files_ignored_and_templates_tracked():
    import subprocess
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    for rel in (
        ".agents/skills/job-application-assistant/01-candidate-profile.md",
        ".agents/skills/job-application-assistant/03-glossary.md",
        ".agents/skills/job-application-assistant/05-profiles.md",
        ".agents/skills/job-scraper/search-config.md",
    ):
        assert rel not in tracked, f"{rel} 은 개인 데이터라 추적하면 안 된다"
        assert rel.replace(".md", ".template.md") in tracked, rel
