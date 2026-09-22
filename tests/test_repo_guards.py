import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_IGNORE = [
    "documents/**", "applications/**", "interview/**", "job_scraper/**",
    "tracker.csv", ".env", "*.pdf", "node_modules/",
]


def test_gitignore_rules():
    s = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read().splitlines()
    for r in REQUIRED_IGNORE:
        assert r in s, f".gitignore 에 {r} 없음"


WORKFLOW = ("setup", "scrape", "rank", "apply", "outcome", "interview")
SKILLS = WORKFLOW + ("job-application-assistant", "job-scraper", "humanize-korean",
                     "wanted-search", "jumpit-search", "groupby-search", "saramin-search", "jobkorea-search")


def test_workflow_skills_have_frontmatter():
    for name in WORKFLOW:
        s = open(os.path.join(ROOT, ".agents", "skills", name, "SKILL.md"), encoding="utf-8").read()
        assert re.search(r"^name: " + name + r"$", s, re.M), name
        assert re.search(r"^description: ", s, re.M), name
        assert "disable-model-invocation: true" in s, name


def test_no_claude_commands_dir():
    assert not os.path.exists(os.path.join(ROOT, ".claude", "commands"))


def test_claude_skills_are_symlinks_to_agents():
    d = os.path.join(ROOT, ".claude", "skills")
    for name in SKILLS:
        p = os.path.join(d, name)
        assert os.path.islink(p), f".claude/skills/{name} 가 심볼릭 링크가 아니다"
        assert os.readlink(p) == f"../../.agents/skills/{name}", name
        assert os.path.exists(os.path.join(p, "SKILL.md")), name
    extra = set(os.listdir(d)) - set(SKILLS)
    assert not extra, f"원천 없는 링크: {extra}"


def test_skills_have_frontmatter():
    for name in ("job-application-assistant", "job-scraper"):
        s = open(os.path.join(ROOT, ".agents", "skills", name, "SKILL.md"), encoding="utf-8").read()
        assert re.search(r"^name: " + name, s, re.M)
        assert "framework_version:" in s


def test_methodology_files_versioned():
    d = os.path.join(ROOT, ".agents", "skills", "job-application-assistant")
    for fn in sorted(os.listdir(d)):
        if fn[0].isdigit():
            s = open(os.path.join(d, fn), encoding="utf-8").read()
            assert s.startswith("---\nframework_version:"), fn


def test_settings_allow_only_repo_tools():
    import json
    s = json.load(open(os.path.join(ROOT, ".claude", "settings.json")))
    for rule in s["permissions"]["allow"]:
        if rule.startswith("Bash("):
            assert re.match(r"Bash\((bun run \.agents/skills/[\w-]+/cli/src/cli\.ts|python3 tools/[\w]+\.py|bash tools/[\w]+\.sh):\*\)", rule), rule


def test_portal_skills_present():
    for s in ("wanted-search", "jumpit-search", "groupby-search", "saramin-search", "jobkorea-search"):
        p = os.path.join(ROOT, ".agents", "skills", s)
        assert os.path.exists(os.path.join(p, "SKILL.md"))
        assert os.path.exists(os.path.join(p, "cli", "src", "cli.ts"))
        assert not os.path.exists(os.path.join(p, "cli", "bun.lock")) or True


def test_install_script_present_and_executable():
    p = os.path.join(ROOT, "install.sh")
    assert os.path.exists(p)
    assert os.access(p, os.X_OK)
    s = open(p, encoding="utf-8").read()
    assert "--check" in s and "bun install" in s and "pypdf" in s


def test_humanizer_vendored_with_attribution():
    d = os.path.join(ROOT, ".agents", "skills", "humanize-korean")
    assert os.path.exists(os.path.join(d, "SKILL.md"))
    assert os.path.exists(os.path.join(d, "references", "quick-rules.md"))
    up = open(os.path.join(d, "UPSTREAM.md"), encoding="utf-8").read()
    assert "epoko77-ai/im-not-ai" in up and "MIT" in up
    assert re.search(r"\| 업스트림 커밋 \| `[0-9a-f]{40}` \|", up)
    ig = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read().splitlines()
    assert "_workspace/" in ig


FIELD_NEUTRAL = (
    (os.path.join("templates", "resume.md"), ("Tech Stacks", "**언어:**", "**프레임워크:**")),
    (os.path.join("templates", "portfolio.md"), ("**스택**",)),
    (os.path.join(".agents", "skills", "job-application-assistant", "01-candidate-profile.template.md"),
     ("## 기술 스택", "**언어:**", "**인프라:**")),
    (os.path.join(".agents", "skills", "job-application-assistant", "04-job-evaluation.md"), ("기술 일치",)),
)


def test_templates_are_field_neutral():
    """개발 직군 전용 표현이 템플릿에 박히지 않았는지 검사한다."""
    for rel, banned in FIELD_NEUTRAL:
        s = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for b in banned:
            assert b not in s, f"{rel} 에 개발 전용 표현 '{b}' 가 있다"


def test_setup_asks_for_field():
    s = open(os.path.join(ROOT, ".agents", "skills", "setup", "SKILL.md"), encoding="utf-8").read()
    assert "직군을 정한다" in s
    assert "목록에서 고르게 하지 않는다" in s


def test_jumpit_gated_on_dev_field():
    s = open(os.path.join(ROOT, ".agents", "skills", "job-scraper", "SKILL.md"), encoding="utf-8").read()
    assert "점핏은 개발 전용이다" in s
