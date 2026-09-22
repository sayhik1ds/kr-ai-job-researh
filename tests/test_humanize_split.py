import json
import humanize_split as H

DOC = """# 이시영 | Backend

> 한 줄 소개다. 두 문장으로 이어진다. 산문이라 윤문 대상이다.

- 이메일: a@b.c · GitHub: https://x/y

## Career

#### 1.1 AMAAQ — 사내 봇 (2026.04 ~ 현재)

자연어로 사내 업무를 처리하는 봇이다. 사내 15명이 쓴다.

**Task**
- 샌드박스 아키텍처 전환: 3단 구조로 전환
- 문서 자동화: MCP 서버 연동

**Tech Stacks** `Java 17` `Docker`

| 항목 | 값 |
|---|---|
| 기간 | 2026.04 |

```bash
echo "코드 블록 안의 문장은 건드리지 않는다"
```

### 상황

여러 라인이 동시에 배포돼 있어 확인이 어려웠다. 실행 위치와 권한이 미해결이었다.
"""


def blocks_of(doc):
    return H.split_blocks(doc)


def test_extracts_only_prose():
    b = blocks_of(DOC)
    bodies = [x[3].strip() for x in b]
    assert any(x.startswith("한 줄 소개다") for x in bodies)
    assert any(x.startswith("자연어로 사내 업무") for x in bodies)
    assert any(x.startswith("여러 라인이 동시에") for x in bodies)
    joined = "\n".join(bodies)
    for excluded in ("샌드박스 아키텍처 전환", "Tech Stacks", "| 항목", "코드 블록 안의", "# 이시영", "이메일:"):
        assert excluded not in joined, excluded


def test_quote_prefix_recorded():
    b = blocks_of(DOC)
    quote = [x for x in b if x[3].strip().startswith("한 줄 소개다")][0]
    assert quote[2].strip() == ">"


def test_short_blocks_dropped():
    assert blocks_of("짧다.\n") == []


def test_round_trip_is_identity(tmp_path):
    src = tmp_path / "doc.md"; src.write_text(DOC, encoding="utf-8")
    out = tmp_path / "h.md"; mp = tmp_path / "h.json"
    assert H.main(["split", str(src), "--out", str(out), "--map", str(mp)]) == 0
    assert H.main(["merge", str(src), "--final", str(out), "--map", str(mp), "--check", "--in-place"]) == 0
    assert src.read_text(encoding="utf-8") == DOC


def test_merge_applies_edits_and_keeps_quote(tmp_path):
    src = tmp_path / "doc.md"; src.write_text(DOC, encoding="utf-8")
    out = tmp_path / "h.md"; mp = tmp_path / "h.json"
    H.main(["split", str(src), "--out", str(out), "--map", str(mp)])
    edited = out.read_text(encoding="utf-8").replace("한 줄 소개다. 두 문장으로 이어진다.", "한 줄 소개다. 두 문장이다.")
    fin = tmp_path / "final.md"; fin.write_text(edited, encoding="utf-8")
    assert H.main(["merge", str(src), "--final", str(fin), "--map", str(mp), "--in-place"]) == 0
    got = src.read_text(encoding="utf-8")
    assert "> 한 줄 소개다. 두 문장이다." in got
    assert "- 샌드박스 아키텍처 전환: 3단 구조로 전환" in got


def test_merge_detects_missing_block(tmp_path, capsys):
    src = tmp_path / "doc.md"; src.write_text(DOC, encoding="utf-8")
    out = tmp_path / "h.md"; mp = tmp_path / "h.json"
    H.main(["split", str(src), "--out", str(out), "--map", str(mp)])
    fin = tmp_path / "final.md"
    fin.write_text("<!-- §1 -->\n한 줄 소개다.\n", encoding="utf-8")
    assert H.main(["merge", str(src), "--final", str(fin), "--map", str(mp)]) == 1


def test_check_catches_changed_number(tmp_path):
    src = tmp_path / "doc.md"; src.write_text(DOC, encoding="utf-8")
    out = tmp_path / "h.md"; mp = tmp_path / "h.json"
    H.main(["split", str(src), "--out", str(out), "--map", str(mp)])
    fin = tmp_path / "final.md"
    fin.write_text(out.read_text(encoding="utf-8").replace("사내 15명이", "사내 20명이"), encoding="utf-8")
    assert H.main(["merge", str(src), "--final", str(fin), "--map", str(mp), "--check"]) == 1
