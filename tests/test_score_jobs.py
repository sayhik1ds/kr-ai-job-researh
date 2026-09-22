import score_jobs as S

CONFIG = """
```drop
프론트|front-?end
시니어|Senior
```

```weights
# 강점
java = 3
llm = 4
# 불일치
php = -4
5년 이상 = -4
[PLACEHOLDER] = 9
```
"""


def test_parse_config():
    drop, w = S.parse_config(CONFIG)
    assert w == {"java": 3, "llm": 4, "php": -4, "5년 이상": -4}
    assert drop.search("프론트엔드 개발자")
    assert drop.search("Senior Backend")
    assert not drop.search("백엔드 개발자")


def test_run_scores_and_drops():
    drop, w = S.parse_config(CONFIG)
    jobs = [
        {"key": "wanted:1", "position": "백엔드 개발자", "text": "Java Spring LLM 서비스"},
        {"key": "wanted:2", "position": "프론트엔드 개발자", "text": "React"},
        {"key": "wanted:3", "position": "PHP 개발자", "text": "php 5년 이상"},
    ]
    scored, dropped = S.run(jobs, drop, w)
    assert [d["key"] for d in dropped] == ["wanted:2"]
    assert scored[0]["key"] == "wanted:1" and scored[0]["score"] == 7
    assert scored[0]["hits"] == ["java", "llm"]
    assert scored[1]["score"] == -8 and "-php" in scored[1]["hits"]


def test_empty_config():
    drop, w = S.parse_config("no blocks")
    assert drop is None and w == {}
