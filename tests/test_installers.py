"""설치 스크립트 두 개가 같은 단계를 덮는지, 윈도우용이 필요한 것을 갖췄는지 검사한다."""
import os, re, stat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, "install.sh")
PS = os.path.join(ROOT, "install.ps1")


def steps(path, pattern):
    return re.findall(pattern, open(path, encoding="utf-8").read())


def test_both_installers_exist():
    assert os.path.exists(SH) and os.path.exists(PS)
    assert os.stat(SH).st_mode & stat.S_IXUSR, "install.sh 에 실행 권한이 없다"


def test_same_steps_covered():
    sh = steps(SH, r'echo "(== [^"]+)"')
    ps = steps(PS, r'Write-Host "(== [^"]+)"')
    assert sh, "install.sh 에 단계 표시가 없다"
    assert set(sh) == set(ps), f"단계 불일치. sh 에만 {set(sh)-set(ps)}, ps 에만 {set(ps)-set(sh)}"


def test_both_have_check_mode():
    assert "--check" in open(SH, encoding="utf-8").read()
    assert "[switch]$Check" in open(PS, encoding="utf-8").read()


def test_both_repair_skill_links():
    for p in (SH, PS):
        s = open(p, encoding="utf-8").read()
        assert "스킬 링크" in s, f"{os.path.basename(p)} 에 링크 복구 단계가 없다"


def test_powershell_handles_windows_specifics():
    s = open(PS, encoding="utf-8").read()
    assert "Junction" in s, "윈도우는 심볼릭 링크 대신 정션으로 복구해야 한다"
    assert r".venv\Scripts\python.exe" in s, "윈도우 venv 경로가 다르다"
    assert "msedge.exe" in s or "chrome.exe" in s, "윈도우 Chrome 경로 탐색이 없다"


def test_build_pdf_is_cross_platform():
    py = os.path.join(ROOT, "tools", "build_pdf.py")
    assert os.path.exists(py), "build_pdf.py 가 없다. bash 없이 PDF 를 못 만든다"
    s = open(py, encoding="utf-8").read()
    assert "chrome.exe" in s and "msedge.exe" in s, "윈도우 Chrome 경로가 없다"
    sh = open(os.path.join(ROOT, "tools", "build_pdf.sh"), encoding="utf-8").read()
    assert "build_pdf.py" in sh, "build_pdf.sh 가 파이썬 구현으로 넘기지 않는다"
