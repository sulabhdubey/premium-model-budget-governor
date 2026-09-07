import hashlib
import json
from zipfile import ZipFile

import pytest

from premium_model_budget_governor.publication import audit_files


def test_private_terms_are_detected_without_echoing_names_or_paths(tmp_path):
    path = tmp_path / 'private-project-name.txt'
    path.write_text('Review Project Aurora before release.')
    report = audit_files([path], ['project aurora'])
    assert report['status'] == 'blocked'
    assert report['findings'][0]['rule'] == 'private_term'
    serialized = json.dumps(report).lower()
    assert 'aurora' not in serialized and str(tmp_path).lower() not in serialized
    assert 'private-project-name' not in serialized


def test_archive_metadata_and_json_escaping_are_scanned(tmp_path):
    path = tmp_path / 'package.whl'
    with ZipFile(path, 'w') as archive:
        archive.writestr('package/METADATA', 'Project Aurora')
        archive.writestr('answers.json', '{"answer":"Project \\u0041urora"}')
    report = audit_files([path], ['project aurora'])
    assert report['status'] == 'blocked'
    assert sum(f['rule'] == 'private_term' for f in report['findings']) == 2


def test_clean_text_never_means_full_privacy_certification(tmp_path):
    path = tmp_path / 'public.md'
    path.write_text('An anonymous bounded task used 200 tokens.')
    report = audit_files([path], ['project aurora'])
    assert report['status'] == 'no_pattern_findings'
    assert report['publication_authorized'] is False
    assert report['files_checked'] == 1
    assert report['input_sha256'] == {'file-0': hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.mark.parametrize('kind', ['binary', 'oversize', 'nested', 'invalid_utf8', 'missing'])
def test_uninspected_content_never_passes(tmp_path, kind):
    path = tmp_path / 'input'
    if kind == 'binary':
        path.write_bytes(b'\x00image')
    elif kind == 'oversize':
        path.write_text('a' * 101)
    elif kind == 'invalid_utf8':
        path.write_bytes(b'\xff\xfe')
    elif kind == 'nested':
        path = tmp_path / 'outer.zip'
        with ZipFile(path, 'w') as archive:
            archive.writestr('inner.zip', b'PK\x03\x04nested')
    report = audit_files([path], ['project aurora'], max_bytes=100 if kind == 'oversize' else 2000)
    assert report['status'] == 'needs_manual_review'
    assert report['uninspected_count'] >= 1


def test_secret_and_personal_path_without_raw_value(tmp_path):
    path = tmp_path / 'note.md'
    path.write_text('ghp_' + 'a' * 30 + '\nC:\\Users\\privateperson\\work')
    result = audit_files([path], [])
    assert {f['rule'] for f in result['findings']} >= {'github_token', 'personal_path'}
    assert 'privateperson' not in json.dumps(result)


def test_archive_total_budget_cannot_be_bypassed(tmp_path):
    path = tmp_path / 'many.zip'
    with ZipFile(path, 'w') as archive:
        for index in range(8):
            archive.writestr(str(index), 'a' * 50)
    result = audit_files([path], [], max_bytes=2000, max_total_bytes=100)
    assert result['status'] == 'needs_manual_review'


@pytest.mark.parametrize('terms', [None, 'secret', [1], [''], ['ab']])
def test_bad_terms_rejected(terms):
    with pytest.raises(ValueError):
        audit_files([], terms)
