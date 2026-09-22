import json
from types import SimpleNamespace
import pytest
import check_evidence as E
import check_submission as S
import track_application as T


def evidence(profile, document, source, claim):
    return {'profile_sha256': E.digest(profile), 'document_sha256': E.digest(document), 'reviewer': 'independent-review',
            'claims': [{'id': 'fact-1', 'claim': claim, 'source_quote': source,
                        'source_context': E.context_at(profile, source), 'document_context': E.context_at(document, claim),
                        'review': {'status': 'supported', 'reason': '동일 프로젝트의 역할과 측정 조건 확인'}}]}


def test_evidence_scope_and_staleness():
    profile = '# A\n30% 개선\n# B\n배포 자동화\n'
    doc = '# B\n30% 개선\n'
    data = evidence(profile, doc, '배포 자동화', '30% 개선')
    assert any('30%' in e for e in E.validate(profile, doc, data))
    assert any('프로필 변경' in e for e in E.validate(profile + '수정', doc, data))


def test_review_and_unmapped_claims_fail():
    p = '# A\n서비스 개발 참여\n'
    d = '# A\n서비스 설계 총괄\n'
    data = evidence(p, d, '서비스 개발 참여', '서비스 설계 총괄')
    data['claims'][0]['review'] = {'status': 'unsupported', 'reason': '역할 과장'}
    assert E.validate(p, d, data)
    data['claims'][0]['review']['status'] = 'supported'
    d += '새로운 근거 없는 경험\n'
    data['document_sha256'] = E.digest(d)
    assert any('미연결' in e for e in E.validate(p, d, data))


def test_context_and_complete_valid_mapping():
    p = '# 회사\n## 프로젝트\n개발 참여\n'
    data = evidence(p, p, '개발 참여', '개발 참여')
    assert E.validate(p, p, data) == []
    data['claims'][0]['source_context'] = ['다른 프로젝트']
    assert any('제목 경로' in e for e in E.validate(p, p, data))


def test_submission_detects_missing_content():
    errors = S.validate('# 문서\n[YOUR_NAME]\n이전회사\n## 동기\n짧음',
        {'required': ['연락처'], 'forbidden': ['이전회사'], 'sections': [{'heading': '동기', 'min': 10, 'max': 20}]})
    assert len(errors) == 4
    assert S.validate('<!-- [YOUR_NAME] -->\n완성', {}) == []


def test_section_count_and_duplicate_heading():
    spec = {'sections': [{'heading': '동기', 'min': 4, 'max': 4, 'count': 'without_spaces'}]}
    assert S.validate('## 동기\n가 나 다 라\n## 다음\n제외', spec) == []
    assert S.validate('## 동기\n가나다라\n## 동기\n중복', spec)
    assert S.validate('## 다른문항\n가나다라', spec)


def create(**kwargs):
    return SimpleNamespace(command='create', portal='wanted', job_id='123', company='회사', position='직무',
                           path='applications/draft', profile='', deadline='', note='', new_attempt=kwargs.get('new_attempt', False))


def update(status='submitted', attempt=1, note=None):
    return SimpleNamespace(command='update', portal='wanted', job_id='123', attempt=attempt, status=status, note=note)


def test_snapshot_and_reapplication(tmp_path):
    draft = tmp_path / 'applications/draft'; draft.mkdir(parents=True)
    (draft / 'resume.pdf').write_bytes(b'pdf-v1')
    T.run(tmp_path, create())
    with pytest.raises(ValueError, match='이미 등록'):
        T.run(tmp_path, create())
    row = T.run(tmp_path, update())
    snapshot = tmp_path / row['snapshot'] / 'resume.pdf'
    (draft / 'resume.pdf').write_bytes(b'pdf-v2')
    assert T.run(tmp_path, update())['history'] == row['history']
    assert snapshot.read_bytes() == b'pdf-v1'
    assert T.run(tmp_path, create(new_attempt=True))['attempt'] == '2'
    second = T.run(tmp_path, update(attempt=2))
    assert (tmp_path / second['snapshot'] / 'resume.pdf').read_bytes() == b'pdf-v2'


def test_failed_archive_preserves_csv(tmp_path):
    T.run(tmp_path, create())
    original = (tmp_path / 'tracker.csv').read_bytes()
    with pytest.raises(ValueError):
        T.run(tmp_path, update())
    assert (tmp_path / 'tracker.csv').read_bytes() == original


def test_legacy_csv_preserves_columns(tmp_path):
    (tmp_path / 'tracker.csv').write_text('date,portal,job_id,company,position,profile,status,deadline,path,note,custom\n2020,wanted,123,회사,직무,,submitted,,applications/old,기존,보존\n')
    row = T.run(tmp_path, update(status='screening', note='검토 중'))
    assert row['custom'] == '보존'
    assert json.loads(row['history'])[0]['note'] == '기존'
    assert json.loads(row['history'])[1]['from'] == 'submitted'
    assert row['attempt'] == '1'


def test_tracker_rolls_back_snapshot_if_csv_write_fails(tmp_path, monkeypatch):
    draft = tmp_path / 'applications/draft'; draft.mkdir(parents=True)
    (draft / 'resume.pdf').write_bytes(b'pdf')
    T.run(tmp_path, create())
    def fail(*args):
        raise OSError('disk error')
    monkeypatch.setattr(T, 'save_rows', fail)
    with pytest.raises(OSError):
        T.run(tmp_path, update())
    assert not (tmp_path / 'documents/applications/wanted_123/attempt_1').exists()
    assert not (tmp_path / '.tracker.lock').exists()


def test_tracker_cannot_overwrite_existing_snapshot(tmp_path):
    draft = tmp_path / 'applications/draft'; draft.mkdir(parents=True)
    (draft / 'resume.pdf').write_bytes(b'pdf')
    T.run(tmp_path, create())
    existing = tmp_path / 'documents/applications/wanted_123/attempt_1'
    existing.mkdir(parents=True)
    (existing / 'keep').write_text('보존')
    with pytest.raises(FileExistsError):
        T.run(tmp_path, update())
    assert (existing / 'keep').read_text() == '보존'


def test_invalid_config_fails_closed(tmp_path):
    config = tmp_path / 'submission.json'
    config.write_text('{"documents": []}')
    assert S.main([str(config)]) == 1
    config.write_text('{"documents": [{"path": "missing.md"}]}')
    assert S.main([str(config)]) == 1


def test_evidence_cli_rejects_empty_claims(tmp_path):
    p = tmp_path / 'profile.md'; p.write_text('프로필')
    d = tmp_path / 'resume.md'; d.write_text('문서')
    e = tmp_path / 'evidence.json'; e.write_text('{}')
    assert E.main([str(p), str(d), str(e)]) == 1


def test_null_review_and_bad_requirement_schema():
    p = '# A\n개발 참여\n'
    data = evidence(p, p, '개발 참여', '개발 참여')
    data['reviewer'] = None
    data['claims'][0]['review']['reason'] = None
    assert len(E.validate(p, p, data)) == 2
    with pytest.raises(ValueError):
        S.validate('문서', {'required': '문서'})
    with pytest.raises(ValueError):
        S.validate('문서', {'sections': [{'heading': '문항', 'min': 10, 'max': 5}]})


def test_pdf_render_does_not_overwrite(tmp_path, monkeypatch):
    import verify_pdf as V
    from pypdf import PdfWriter
    pdf = tmp_path / 'test.pdf'
    writer = PdfWriter(); writer.add_blank_page(width=200, height=200)
    writer.write(pdf)
    directory = tmp_path / 'pages'; directory.mkdir()
    keep = directory / 'keep'; keep.write_text('keep')
    monkeypatch.setattr(V.shutil, 'which', lambda name: '/test/pdftoppm')
    assert V.main([str(pdf), '--render-dir', str(directory)]) == 1
    assert keep.read_text() == 'keep'


def test_pdf_missing_renderer_is_incomplete(tmp_path, monkeypatch):
    import verify_pdf as V
    from pypdf import PdfWriter
    pdf = tmp_path / 'test.pdf'
    writer = PdfWriter(); writer.add_blank_page(width=200, height=200)
    writer.write(pdf)
    monkeypatch.setattr(V.shutil, 'which', lambda name: None)
    assert V.main([str(pdf), '--render-dir', str(tmp_path / 'pages')]) == 2
