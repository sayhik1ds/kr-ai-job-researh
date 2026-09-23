#!/usr/bin/env python3
"""코덱스가 이 저장소의 스킬을 읽을 수 있는지 검사한다.

코덱스 CLI 는 cwd 에서 저장소 루트(`.git` 이 있는 곳)까지 올라가며 `<dir>/.agents/skills`
를 훑는다. 각 `SKILL.md` 의 YAML frontmatter 에서 `name` 과 `description` 만 읽고
나머지 필드는 무시한다. 이 도구가 그 조건을 그대로 확인한다.

  python3 tools/check_codex_skills.py [--json]

검사 항목
  1. `.agents/skills/<이름>/SKILL.md` 가 저장소 루트 아래에 있다
  2. frontmatter 가 YAML 로 파싱된다. 따옴표 없는 콜론은 파싱을 깨뜨린다
  3. `name` 이 있고 64자 이하이며 디렉토리 이름과 같다
  4. `description` 이 있고 비어 있지 않다
  5. 이름이 중복되지 않는다
  6. description 총합이 8,000자 이하다. 코덱스는 턴 시작 시 목록을 이 상한으로 자른다
  7. 클로드 코드용 `.claude/skills/<이름>` 심볼릭 링크가 같은 대상을 가리킨다

이 검사는 정적이다. 실제 로딩은 2026-09-23 에 Codex CLI 0.155.1 에서
`/skills` 로 스킬 14개가 모두 표시되는 것을 확인했다. 이후로는 이 도구가
회귀만 잡는다.
"""
import argparse, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(ROOT, ".agents", "skills")
CLAUDE = os.path.join(ROOT, ".claude", "skills")
NAME_MAX = 64
LIST_BUDGET = 8000
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def parse_frontmatter(text):
    """코덱스 파서와 같은 범위만 본다. name, description, 그리고 YAML 유효성."""
    m = FM.match(text)
    if not m:
        return None, "frontmatter 블록이 없다"
    body = m.group(1)
    try:
        import yaml
        data = yaml.safe_load(body)
        if not isinstance(data, dict):
            return None, "frontmatter 가 매핑이 아니다"
        return data, None
    except ImportError:
        pass
    except Exception as e:
        return None, f"YAML 파싱 실패: {str(e).splitlines()[0]}"
    # yaml 이 없으면 최소 파싱. 블록 스칼라(>, |)를 처리한다
    data, key, buf = {}, None, []
    for line in body.split("\n"):
        m2 = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m2 and not line.startswith(" "):
            if key:
                data[key] = "\n".join(buf).strip()
            key, first = m2.group(1), m2.group(2).strip()
            buf = [] if first in (">", "|", ">-", "|-") else [first]
        elif key is not None:
            buf.append(line.strip())
    if key:
        data[key] = "\n".join(buf).strip()
    return data, None


def check():
    problems, skills = [], []
    if not os.path.isdir(AGENTS):
        return [f"{AGENTS} 가 없다"], []
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        problems.append(".git 이 없다. 코덱스가 저장소 루트를 못 찾아 상위 탐색이 멈춘다")

    for name in sorted(os.listdir(AGENTS)):
        d = os.path.join(AGENTS, name)
        if not os.path.isdir(d):
            continue
        p = os.path.join(d, "SKILL.md")
        if not os.path.exists(p):
            problems.append(f"{name}: SKILL.md 가 없다. 코덱스가 스킬로 보지 않는다")
            continue
        data, err = parse_frontmatter(open(p, encoding="utf-8").read())
        if err:
            problems.append(f"{name}: {err}")
            continue
        n = str(data.get("name") or name)
        desc = str(data.get("description") or "").strip()
        if not data.get("name"):
            problems.append(f"{name}: name 이 없다. 코덱스는 폴더 이름으로 대체하지만 명시하는 편이 낫다")
        elif n != name:
            problems.append(f"{name}: name 이 '{n}' 이라 디렉토리 이름과 다르다")
        if len(n) > NAME_MAX:
            problems.append(f"{name}: name 이 {len(n)}자다. 상한 {NAME_MAX}자")
        if not desc:
            problems.append(f"{name}: description 이 비었다. 코덱스가 스킬을 버린다")
        skills.append({"name": n, "desc_chars": len(desc), "path": os.path.relpath(p, ROOT)})

    seen = {}
    for s in skills:
        seen.setdefault(s["name"], []).append(s["path"])
    for n, paths in seen.items():
        if len(paths) > 1:
            problems.append(f"이름 중복 '{n}': {paths}")

    total = sum(s["desc_chars"] for s in skills)
    if total > LIST_BUDGET:
        problems.append(f"description 총합 {total}자로 상한 {LIST_BUDGET}자를 넘는다. 목록이 잘린다")

    for s in skills:
        link = os.path.join(CLAUDE, s["name"])
        if not os.path.islink(link):
            problems.append(f"{s['name']}: .claude/skills 심볼릭 링크가 없다. 클로드 코드에서 안 보인다")
        elif os.readlink(link) != f"../../.agents/skills/{s['name']}":
            problems.append(f"{s['name']}: 심볼릭 링크 대상이 '{os.readlink(link)}' 다")

    return problems, skills


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    problems, skills = check()
    total = sum(s["desc_chars"] for s in skills)
    if a.json:
        print(json.dumps({"skills": skills, "problems": problems, "desc_total": total}, ensure_ascii=False, indent=1))
    else:
        for s in skills:
            print(f"  {s['name']:<28} description {s['desc_chars']:>4}자")
        print(f"\n스킬 {len(skills)}개, description 총합 {total}자 / 상한 {LIST_BUDGET}자")
        for p in problems:
            print(f"  FAIL {p}")
        print("OK: 코덱스 탐색 조건을 모두 만족한다" if not problems else f"\n{len(problems)}건 실패")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
