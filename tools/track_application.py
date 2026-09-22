#!/usr/bin/env python3
"""기존 tracker.csv를 보존하며 지원 회차·상태 이력·제출본을 관리한다.
사용: python3 tools/track_application.py create --portal wanted --job-id 123 --company 회사 --position 직무 --path applications/초안
      python3 tools/track_application.py update --portal wanted --job-id 123 --attempt 1 --status submitted
      python3 tools/track_application.py list
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FIELDS = 'date portal job_id company position profile status deadline path note attempt history snapshot'.split()
STATUSES = {'drafted', 'submitted', 'screening', 'interview_1', 'interview_2', 'offer', 'rejected', 'withdrawn', 'no_response', 'expired'}
TERMINAL = {'offer', 'rejected', 'withdrawn', 'expired'}


def now():
    return datetime.now(timezone.utc).isoformat()


def key(portal, job_id):
    if not re.fullmatch(r'[a-z][a-z0-9-]*', portal) or not re.fullmatch(r'[A-Za-z0-9_-]+', job_id):
        raise ValueError('포털과 공고 ID는 영문·숫자·하이픈·밑줄만 허용')
    return portal + '_' + job_id


def read_rows(path):
    if not path.exists():
        return [], FIELDS[:]
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if not {'portal', 'job_id', 'status', 'path'} <= set(fields):
            raise ValueError('tracker.csv 필수 열 누락')
        rows = list(reader)
        if any(None in r for r in rows):
            raise ValueError('tracker.csv 열 수 불일치')
        return rows, fields + [f for f in FIELDS if f not in fields]


def save_rows(path, rows, fields):
    fd, tmp = tempfile.mkstemp(prefix='.tracker-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(rows)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def archive(root, row, destination):
    source = (root / row['path']).resolve()
    if not source.is_dir() or not source.is_relative_to((root / 'applications').resolve()):
        raise ValueError('초안 경로는 applications/ 아래의 폴더여야 함')
    files = sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in {'.md', '.pdf', '.json'})
    if not files or not any(p.suffix.lower() == '.pdf' for p in files):
        raise ValueError('제출할 PDF가 없음')
    if any(p.is_symlink() or not p.resolve().is_relative_to(source) for p in files):
        raise ValueError('제출 폴더 밖의 파일이나 심볼릭 링크는 보관할 수 없음')
    destination.mkdir(parents=True, exist_ok=False)
    try:
        hashes = {}
        for path in files:
            rel = path.relative_to(source)
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            hashes[str(rel)] = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = destination / '_submission_manifest.json'
        if manifest.exists():
            raise ValueError('예약 파일명 _submission_manifest.json이 초안에 있음')
        manifest.write_text(json.dumps({'submitted_at': now(), 'files': hashes}, ensure_ascii=False, indent=2))
    except Exception:
        shutil.rmtree(destination)
        raise


def run(root, args):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.tracker.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('다른 기록 작업 실행 중. 종료된 작업이면 .tracker.lock을 확인')
    os.close(fd)
    created = None
    try:
        path = root / 'tracker.csv'
        rows, fields = read_rows(path)
        if args.command == 'list':
            return rows
        identity = key(args.portal, args.job_id)
        matches = [r for r in rows if r['portal'] == args.portal and r['job_id'] == args.job_id]
        if args.command == 'create':
            if matches and not args.new_attempt:
                raise ValueError('이미 등록된 공고. 재지원이면 --new-attempt 사용')
            attempt = max([int(r.get('attempt') or 1) for r in matches], default=0) + 1
            row = dict.fromkeys(fields, '')
            row.update(date=now(), portal=args.portal, job_id=args.job_id, company=args.company,
                       position=args.position, profile=args.profile, status='drafted', deadline=args.deadline,
                       path=args.path, note=args.note, attempt=str(attempt),
                       history=json.dumps([{'at': now(), 'from': None, 'to': 'drafted', 'note': args.note}], ensure_ascii=False))
            rows.append(row)
        else:
            chosen = [r for r in matches if int(r.get('attempt') or 1) == args.attempt]
            if len(chosen) != 1:
                raise ValueError('지원 기록이 없거나 중복됨. list로 확인 후 회차를 지정')
            row = chosen[0]
            previous = row['status']
            if args.status not in STATUSES:
                raise ValueError('알 수 없는 상태')
            if args.status == 'drafted' and previous != 'drafted':
                raise ValueError('초안으로 되돌릴 수 없음. 재지원은 새 회차 사용')
            if previous in TERMINAL and args.status != previous:
                raise ValueError('종료된 지원. 재지원은 새 회차 사용')
            if args.status == 'submitted' and previous not in {'drafted', 'submitted'}:
                raise ValueError('제출 상태로 되돌릴 수 없음. 재지원은 새 회차 사용')
            history = json.loads(row.get('history') or '[]')
            if not isinstance(history, list):
                raise ValueError('상태 이력 형식 오류')
            if not history:
                history.append({'at': now(), 'from': None, 'to': previous,
                                'note': row.get('note') or '', 'legacy_import': True})
            if args.status == 'submitted' and previous == 'drafted':
                destination = root / 'documents' / 'applications' / identity / f'attempt_{args.attempt}'
                archive(root, row, destination)
                created = destination
                row['snapshot'] = str(destination.relative_to(root))
            # 동일 상태의 재실행은 제출본과 이력을 중복 생성하지 않는다.
            if previous != args.status or (args.note is not None and args.note != row.get('note')):
                history.append({'at': now(), 'from': previous, 'to': args.status, 'note': args.note or ''})
            row.update(status=args.status, attempt=str(args.attempt), history=json.dumps(history, ensure_ascii=False))
            if args.note is not None:
                row['note'] = args.note
        save_rows(path, rows, fields)
        return row
    except Exception:
        if created is not None:
            shutil.rmtree(created)
        raise
    finally:
        lock.unlink()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default='.')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    for command in ('create', 'update'):
        q = sub.add_parser(command)
        q.add_argument('--portal', required=True); q.add_argument('--job-id', required=True)
        q.add_argument('--note', default='' if command == 'create' else None)
        if command == 'create':
            for field in ('company', 'position', 'path'):
                q.add_argument('--' + field, required=True)
            q.add_argument('--profile', default=''); q.add_argument('--deadline', default='')
            q.add_argument('--new-attempt', action='store_true')
        else:
            q.add_argument('--attempt', required=True, type=int)
            q.add_argument('--status', required=True, choices=sorted(STATUSES))
    args = p.parse_args(argv)
    try:
        result = run(args.root, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as e:
        print(f'FAIL: {e}'); return 1


if __name__ == '__main__':
    raise SystemExit(main())
