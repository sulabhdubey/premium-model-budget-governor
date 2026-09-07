"""Bounded, read-only publication checks with no source text in reports."""

import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
from zipfile import BadZipFile, ZipFile, is_zipfile

from .scanners import SECRET_PATTERNS


def _normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalnum())


def audit_files(paths, forbidden_terms, *, max_bytes=2_000_000, max_total_bytes=20_000_000):
    if (not isinstance(forbidden_terms, list) or len(forbidden_terms) > 200
            or any(not isinstance(t, str) or not 3 <= len(t) <= 200
                   or len(_normalized(t)) < 3 for t in forbidden_terms)):
        raise ValueError('terms must be a bounded list of nonempty private phrases')
    for value in (max_bytes, max_total_bytes):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError('inspection bounds must be positive integers')
    paths = list(paths)
    if len(paths) > 2000:
        raise ValueError('too many explicit files')
    terms = [_normalized(t) for t in forbidden_terms]
    findings, uninspected = [], []
    digests = {}
    checked, total = 0, 0

    def flag(identifier, rule):
        finding = {'item': identifier, 'rule': rule}
        if finding not in findings:
            findings.append(finding)

    def scan(data, identifier):
        nonlocal checked
        if b'\x00' in data:
            uninspected.append({'item': identifier, 'reason': 'binary_requires_manual_review'})
            return
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            uninspected.append({'item': identifier, 'reason': 'encoding_requires_manual_review'})
            return
        checked += 1
        # Decode JSON escapes so a string hidden behind unicode escapes is inspected.
        try:
            decoded = json.loads(text)
        except (ValueError, RecursionError):
            decoded = None
        if decoded is not None:
            text += '\n' + json.dumps(decoded, ensure_ascii=False)
        normalized = _normalized(text)
        if any(term in normalized for term in terms):
            flag(identifier, 'private_term')
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                flag(identifier, name)
        if re.search(r'(?:[A-Za-z]:[/\\]+Users[/\\]+[^\s/\\]+|/(?:home|Users)/[^\s/]+)', text):
            flag(identifier, 'personal_path')

    def content(data, identifier, *, nested=False):
        nonlocal total
        if is_zipfile(io.BytesIO(data)):
            if nested:
                uninspected.append({'item': identifier, 'reason': 'nested_archive'})
                return
            try:
                with ZipFile(io.BytesIO(data)) as archive:
                    entries = archive.infolist()
                    if len(entries) > 2000:
                        uninspected.append({'item': identifier, 'reason': 'archive_entry_limit'})
                        return
                    for index, entry in enumerate(entries):
                        if entry.is_dir():
                            continue
                        child = f'{identifier}:{index}'
                        # Names can also disclose identity; never include them in reports.
                        if any(term in _normalized(entry.filename) for term in terms):
                            flag(child, 'private_term')
                        if entry.file_size > max_bytes or total + entry.file_size > max_total_bytes:
                            uninspected.append({'item': child, 'reason': 'inspection_limit'})
                            continue
                        if entry.flag_bits & 1:
                            uninspected.append({'item': child, 'reason': 'encrypted_archive_entry'})
                            continue
                        with archive.open(entry) as stream:
                            payload = stream.read(max_bytes + 1)
                        total += len(payload)
                        if len(payload) > max_bytes:
                            uninspected.append({'item': child, 'reason': 'inspection_limit'})
                        elif entry.filename.lower().endswith(('.zip', '.whl')):
                            uninspected.append({'item': child, 'reason': 'nested_archive'})
                        else:
                            content(payload, child, nested=True)
            except (OSError, BadZipFile, RuntimeError, NotImplementedError):
                uninspected.append({'item': identifier, 'reason': 'archive_unreadable'})
        else:
            scan(data, identifier)

    for index, value in enumerate(paths):
        identifier = f'file-{index}'
        path = Path(value)
        if any(term in _normalized(path.name) for term in terms):
            flag(identifier, 'private_term')
        try:
            if path.is_symlink() or not path.is_file():
                raise OSError('not a regular file')
            if path.stat().st_size > max_bytes or total + path.stat().st_size > max_total_bytes:
                uninspected.append({'item': identifier, 'reason': 'inspection_limit'})
                continue
            with path.open('rb') as stream:
                data = stream.read(max_bytes + 1)
            if len(data) > max_bytes:
                uninspected.append({'item': identifier, 'reason': 'inspection_limit'})
                continue
            total += len(data)
            digests[identifier] = hashlib.sha256(data).hexdigest()
            content(data, identifier)
        except OSError:
            uninspected.append({'item': identifier, 'reason': 'file_unreadable'})
    return {'schema_version': 1, 'status': ('blocked' if findings else
            'needs_manual_review' if uninspected or not paths else 'no_pattern_findings'),
            'publication_authorized': False, 'files_checked': checked,
            'input_sha256': digests,
            'input_files': len(paths), 'findings': findings,
            'uninspected_count': len(uninspected), 'uninspected': uninspected,
            'limitations': ['Pattern checks cannot identify every confidential fact or secret.',
                            'Images and uninspected content require manual review.',
                            'No history, remote deletion, malware guarantee or publication authorization.']}
