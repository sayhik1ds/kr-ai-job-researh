#!/usr/bin/env python3
"""주장별 근거와 독립 검토 기록을 검증한다. 의미 판단은 리뷰 에이전트가 맡는다.
사용: python3 tools/check_evidence.py <profile.md> <document.md> <evidence.json>
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from check_facts import check


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def visible(text):
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def context_at(text, quote):
    """고유 인용문 앞의 제목 계층. 줄 번호를 저장하지 않는다."""
    pos = text.index(quote)
    stack = []
    for m in re.finditer(r'^(#{1,6})\s+(.+)$', text[:pos], re.M):
        level = len(m[1])
        stack = [(n, title) for n, title in stack if n < level]
        stack.append((level, m[2].strip()))
    return [title for _, title in stack]


def validate(profile, document, data):
    errors = []
    if data.get('profile_sha256') != digest(profile):
        errors.append('프로필 변경: 근거를 다시 검토해야 함')
    if data.get('document_sha256') != digest(document):
        errors.append('문서 변경: 근거를 다시 검토해야 함')
    if not isinstance(data.get('reviewer'), str) or not data['reviewer'].strip():
        errors.append('독립 리뷰 에이전트 식별자 누락')
    claims = data.get('claims')
    if not isinstance(claims, list) or not claims:
        return errors + ['claims 목록이 비어 있음']
    source, output = visible(profile), visible(document)
    covered = [False] * len(output)
    ids = set()
    for c in claims:
        if not isinstance(c, dict):
            errors.append('주장 형식 오류')
            continue
        key = c.get('id')
        if not isinstance(key, str) or not key or key in ids:
            errors.append('근거 ID 누락 또는 중복')
        ids.add(str(key))
        quote, original = c.get('claim', ''), c.get('source_quote', '')
        if not isinstance(quote, str) or not quote.strip() or output.count(quote) != 1:
            errors.append(f'{key}: 문서 인용은 정확히 한 곳과 일치해야 함')
            continue
        if not isinstance(original, str) or not original.strip() or source.count(original) != 1:
            errors.append(f'{key}: 프로필 인용은 정확히 한 곳과 일치해야 함')
            continue
        for field, text, excerpt in [('document_context', output, quote), ('source_context', source, original)]:
            if c.get(field) != context_at(text, excerpt):
                errors.append(f'{key}: {field} 제목 경로 불일치')
        # 다른 프로젝트의 숫자를 재사용해도 해당 근거에 없으면 실패한다.
        errors.extend(f'{key}: {e}' for e in check(original, quote))
        review = c.get('review', {})
        if (not isinstance(review, dict) or review.get('status') != 'supported'
                or not isinstance(review.get('reason'), str) or not review['reason'].strip()):
            errors.append(f'{key}: 프로젝트·역할·측정 조건의 의미 검토 미완료')
        start = output.index(quote)
        covered[start:start + len(quote)] = [True] * len(quote)
    # 제목과 구분선을 제외한 모든 본문 행을 매핑해야 한다. 누락을 조용히 통과시키지 않는다.
    offset = 0
    for line in output.splitlines(keepends=True):
        stripped = line.strip()
        if stripped and not re.match(r'^(#{1,6}\s|[-*_]{3,}$)', stripped):
            for i, char in enumerate(line):
                if char.isalnum() and not covered[offset + i]:
                    errors.append('근거 미연결 본문: ' + stripped[:100])
                    break
        offset += len(line)
    return errors


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile'); p.add_argument('document'); p.add_argument('evidence')
    a = p.parse_args(argv)
    try:
        data = json.loads(Path(a.evidence).read_text())
        if not isinstance(data, dict):
            raise ValueError('근거 파일은 JSON 객체여야 함')
        errors = validate(Path(a.profile).read_text(), Path(a.document).read_text(), data)
    except (OSError, ValueError, TypeError) as e:
        print(f'FAIL: {e}'); return 1
    for e in errors:
        print('FAIL: ' + e)
    if not errors:
        print('OK: 근거 연결·범위·검토 기록 확인. 의미의 정확성은 독립 리뷰 결과에 의존함')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
