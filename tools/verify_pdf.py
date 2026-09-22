#!/usr/bin/env python3
"""PDF 쪽수와 텍스트 레이어를 검사한다.

사용:
  python3 tools/verify_pdf.py <pdf> [--max-pages N] [--expect 문자열 ...]

--expect 는 텍스트 레이어에 반드시 있어야 하는 문자열(이름·이메일 등).
pypdf가 없으면 종료 코드 2.
"""
import argparse, sys
import shutil
import subprocess
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--expect", nargs="*", default=[])
    ap.add_argument("--render-dir", help="pdftoppm으로 페이지 PNG 생성. 기존 폴더에는 덮어쓰지 않음")
    a = ap.parse_args(argv)
    try:
        from pypdf import PdfReader
    except ImportError:
        import os
        venv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "bin", "python")
        # .venv/bin/python 은 시스템 파이썬의 심볼릭 링크라 경로 비교로는 구분이 안 된다. 환경변수로 재실행을 1회 제한한다.
        if os.path.exists(venv) and not os.environ.get("AJSKR_VENV_REEXEC"):
            os.environ["AJSKR_VENV_REEXEC"] = "1"
            os.execve(venv, [venv] + sys.argv, os.environ)
        print("pypdf가 없다. bash install.sh 를 실행하거나 pip install pypdf", file=sys.stderr)
        return 2
    r = PdfReader(a.pdf)
    n = len(r.pages)
    text = "\n".join((p.extract_text() or "") for p in r.pages)
    ok = True
    print(f"쪽수: {n}")
    if a.max_pages is not None and n > a.max_pages:
        print(f"FAIL: {a.max_pages}쪽 초과")
        ok = False
    if not text.strip():
        print("FAIL: 텍스트 레이어가 비었다")
        ok = False
    for i, page in enumerate(r.pages, 1):
        if not (page.extract_text() or '').strip():
            print(f"확인 필요: {i}쪽에 추출 가능한 텍스트가 없음. 이미지 페이지인지 빈 페이지인지 시각 검토")
    for s in a.expect:
        if s not in text:
            print(f"FAIL: 텍스트에 '{s}' 없음")
            ok = False
    if a.render_dir:
        if not shutil.which('pdftoppm'):
            print('FAIL: PDF 시각 검토용 pdftoppm이 없음. Poppler 설치 필요')
            return 2
        directory = Path(a.render_dir)
        try:
            directory.mkdir(parents=True, exist_ok=False)
            subprocess.run(['pdftoppm', '-png', '-r', '110', str(Path(a.pdf).resolve()), str(directory / 'page')], check=True, capture_output=True)
            if len(list(directory.glob('page-*.png'))) != n:
                print('FAIL: PDF 쪽수와 생성된 이미지 수가 다름')
                return 1
        except (OSError, subprocess.CalledProcessError) as e:
            print(f'FAIL: 페이지 이미지 생성 실패: {e}')
            return 1
        print(f'시각 검토 필요: {directory}의 모든 페이지에서 잘림·빈 페이지·겹침 확인')
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
