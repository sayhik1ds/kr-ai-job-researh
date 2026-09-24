#!/usr/bin/env python3
"""마크다운 → PDF. pandoc 으로 HTML 을 만들고 Chrome 헤드리스로 인쇄한다.

  python3 tools/build_pdf.py <in.md> <out.pdf> [resume|doc]

맥·리눅스·윈도우에서 같이 돈다. Chrome 경로는 자동으로 찾고, 못 찾으면
`CHROME_BIN` 환경변수를 본다. Edge 도 같은 엔진이라 대체로 쓸 수 있다.

pandoc 옵션 두 개가 중요하다.
  --metadata title=""   없으면 pandoc 이 제목 블록을 넣어 H1 과 겹친다
  hard_line_breaks      없으면 `**기간**` / `**역할**` 줄이 한 줄로 합쳐진다
"""
import argparse, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = {"resume": "resume.css", "doc": "doc.css"}

CHROME_CANDIDATES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME_ON_PATH = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]


def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    for c in CHROME_ON_PATH:
        p = shutil.which(c)
        if p:
            return p
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("mode", nargs="?", default="doc", choices=sorted(CSS))
    ap.add_argument("--keep-html", action="store_true", help="중간 HTML 을 지우지 않는다")
    a = ap.parse_args(argv)

    if not os.path.exists(a.src):
        print(f"입력 파일이 없다: {a.src}", file=sys.stderr)
        return 2
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("pandoc 이 없다. https://pandoc.org/installing.html", file=sys.stderr)
        return 2
    chrome = find_chrome()
    if not chrome:
        print("Chrome 을 찾지 못했다. 설치하거나 CHROME_BIN 환경변수로 경로를 준다", file=sys.stderr)
        return 2

    css = os.path.join(ROOT, "templates", "assets", CSS[a.mode])
    fd, html = tempfile.mkstemp(prefix="ajskr_", suffix=".html")
    os.close(fd)
    out_abs = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)
    try:
        subprocess.run(
            [pandoc, a.src, "-f", "gfm+hard_line_breaks", "-t", "html5", "-s",
             "--metadata", "title=", "-c", css, "--embed-resources", "-o", html],
            check=True)
        url = "file:///" + html.replace("\\", "/").lstrip("/")
        subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={out_abs}", url],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"빌드 실패 (종료 코드 {e.returncode})", file=sys.stderr)
        return 1
    finally:
        if not a.keep_html:
            try:
                os.remove(html)
            except OSError:
                pass
    if not os.path.exists(out_abs):
        print("PDF 가 만들어지지 않았다", file=sys.stderr)
        return 1
    print(out_abs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
