#!/usr/bin/env python3
"""제출 문서의 placeholder, 필수 문구, 금지 문구, 문항별 글자 수를 검사한다.
사용: python3 tools/check_submission.py <requirements.json>
문서 경로는 설정 파일의 폴더를 기준으로 해석한다. 네트워크 요청은 하지 않는다.
"""
import argparse
import json
import re
from pathlib import Path


def plain(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'!\[([^]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'^\s*(?:#{1,6}\s+|>\s?|[-*+]\s+)', '', text, flags=re.M)
    return text.replace('**', '').replace('`', '').strip()


def validate(text, spec):
    if not isinstance(spec, dict):
        raise ValueError('문서 설정은 JSON 객체여야 함')
    for field in ('required', 'forbidden'):
        values = spec.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError(field + '는 비어 있지 않은 문자열의 목록이어야 함')
    sections = spec.get('sections', [])
    if not isinstance(sections, list):
        raise ValueError('sections는 목록이어야 함')
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('heading'), str) or not section['heading'].strip():
            raise ValueError('문항 제목 누락')
        for field in ('min', 'max'):
            if field in section and (type(section[field]) is not int or section[field] < 0):
                raise ValueError('문항 글자 수 제한은 0 이상의 정수여야 함')
        if section.get('min', 1) > section.get('max', float('inf')):
            raise ValueError('최소 글자 수가 최대 글자 수보다 큼')
    errors = []
    body = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    if not body.strip():
        errors.append('빈 문서')
    for token in sorted(set(re.findall(r'\[[A-Z][A-Z_0-9]*\]|\bTODO\b|\bTBD\b', body))):
        errors.append('미완성 표기: ' + token)
    rendered = plain(body)
    for value in spec.get('required', []):
        if value not in rendered:
            errors.append('필수 문구 누락: ' + value)
    for value in spec.get('forbidden', []):
        if value and value in rendered:
            errors.append('금지 문구 잔존: ' + value)
    for section in spec.get('sections', []):
        heading = section['heading']
        matches = list(re.finditer(r'^#{1,6}\s+(.+?)\s*$', body, re.M))
        found = [i for i, m in enumerate(matches) if m[1] == heading]
        if len(found) != 1:
            errors.append('문항 제목 누락 또는 중복: ' + heading)
            continue
        i = found[0]
        level = len(matches[i][0]) - len(matches[i][0].lstrip('#'))
        end = len(body)
        for following in matches[i+1:]:
            next_level = len(following[0]) - len(following[0].lstrip('#'))
            if next_level <= level:
                end = following.start(); break
        answer = plain(body[matches[i].end():end])
        mode = section.get('count', 'with_spaces')
        if mode not in ('with_spaces', 'without_spaces'):
            errors.append('글자 수 계산 방식 오류: ' + mode); continue
        count = len(re.sub(r'\s', '', answer) if mode == 'without_spaces' else answer)
        if not answer or not section.get('min', 1) <= count <= section.get('max', float('inf')):
            errors.append(f'{heading}: 답변 {count}자, 허용 {section.get("min", 1)}~{section.get("max", "제한 없음")}자')
    return errors


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('requirements')
    a = p.parse_args(argv)
    try:
        config = Path(a.requirements)
        specs = json.loads(config.read_text())['documents']
        if not isinstance(specs, list) or not specs:
            raise ValueError('documents 목록이 비어 있음')
        errors = []
        for spec in specs:
            path = config.parent / spec['path']
            if path.suffix.lower() != '.md':
                raise ValueError('검사 대상은 .md 파일이어야 함')
            errors.extend(f'{path.name}: {e}' for e in validate(path.read_text(), spec))
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f'FAIL: {e}'); return 1
    for e in errors:
        print('FAIL: ' + e)
    if not errors:
        print('OK: 제출 문구·미완성 표기·문항 분량 검사 통과')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
