import json, os
import merge_jobs as M
import rank_table as R


def test_portal_of():
    assert M.portal_of("/x/job_scraper/raw/wanted_q1.json") == "wanted"
    assert M.portal_of("saramin_browse.json") == "saramin"
    assert M.portal_of("misc.json") is None


def test_norm_builds_text_and_key():
    j = M.norm("jumpit", {"id": 7, "title": "백엔드", "company": "A", "techStacks": ["Java", "Spring"], "career": "0~3년", "due": "2026-10-01"})
    assert j["key"] == "jumpit:7" and j["years"] == "0~3년"
    assert "Java" in j["text"] and "백엔드" in j["text"]
    assert M.norm("wanted", {"title": "no id"}) is None


def test_merge_dedup_and_seen(tmp_path, monkeypatch):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "wanted_a.json").write_text(json.dumps({"results": [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]}), encoding="utf-8")
    (raw / "wanted_b.json").write_text(json.dumps({"results": [{"id": "2", "title": "B"}, {"id": "3", "title": "C"}]}), encoding="utf-8")
    seen = tmp_path / "seen.json"; seen.write_text(json.dumps(["wanted:3"]), encoding="utf-8")
    out = tmp_path / "jobs.json"
    M.main([str(raw / "*.json"), "--out", str(out), "--seen", str(seen), "--bookmarks", str(tmp_path / "none.json")])
    keys = [j["key"] for j in json.load(open(out, encoding="utf-8"))]
    assert keys == ["wanted:1", "wanted:2"]


def test_rank_table_orders_by_total(tmp_path, capsys):
    d = tmp_path / "rank"; d.mkdir()
    for k, t, v in (("a", 60, "격차 확인 후 지원"), ("b", 85, "지원 권장"), ("c", 40, "보류")):
        (d / f"{k}.json").write_text(json.dumps({"key": k, "company": k, "position": "p", "scores": {"total": t}, "verdict": v, "gate": {"years": "통과"}, "gaps": []}), encoding="utf-8")
    out = tmp_path / "rank.json"
    R.main(["--dir", str(d), "--out", str(out)])
    rows = json.load(open(out, encoding="utf-8"))
    assert [r["key"] for r in rows] == ["b", "a", "c"]
    assert "| 1 | 85 |" in capsys.readouterr().out
