"""Scan an exact restored private cache; emit hashes/rule locations only."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import tempfile

KEYS = ('intel-state-Linux-37620143441-1', 'intel-state-Linux-37463197318-1')
FILES = ('intel_state.json', 'provider_changes.json', 'provider_state.json',
         'project_evaluations.json', 'delivery_receipts.json', 'news.db',
         'health.json', 'feed_health.json')
FILE_LIMIT = 32 * 1024 * 1024
TOTAL_LIMIT = 128 * 1024 * 1024
RULES = (
 ('personal_windows_home', r'(?i)(?<![a-z])(?:[a-z]:[/\\])Users[/\\](?!Public\b|runneradmin\b)[^\s<>"\x27]+'),
 ('private_network_url', r'(?i)\bhttps?://(?:localhost\b|127\.\d+\.\d+\.\d+\b|0\.0\.0.0\b|10\.\d+\.\d+\.\d+\b|192\.168\.\d+\.\d+\b|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+\b|\[::1\])'),
 ('personal_project_material', r'(?i)\b(?:Hearth\s+POS|fruit[- ]slicer|gesture[- ]control)\b|id=["\x27]project-shortlists["\x27]'),
 ('operational_report_section', r'(?i)id=["\x27](?:providers|provider-status|provider-actions|provider-changes|project-shortlists)["\x27]'),
 ('operational_data_field', r'(?i)["\x27](?:probe_evidence|probe_source|bound_model_routes|routed_via|private_coverage|provider_actions)["\x27]\s*:'),
 ('sensitive_assignment', r'(?i)\b(?:api[_-]?key|auth[_-]?token|github[_-]?token|telegram[_-]?(?:bot[_-]?)?token|discord[_-]?(?:bot[_-]?)?token|password|client[_-]?secret)["\x27]?\s*[=:]\s*["\x27]?([A-Za-z0-9_+/=-]{16,})'),
 ('vendor_credential_shape', r'(?<![A-Za-z0-9_])(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|sk-(?:proj-|or-v1-|ant-[A-Za-z0-9_-]*-)?[A-Za-z0-9_-]{32,}|AIza[A-Za-z0-9_-]{35}|AKIA[A-Z0-9]{16}|\d{8,12}:[A-Za-z0-9_-]{32,}|[A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,})'),
 ('private_key_material', r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
)
PATTERNS = [(rule, re.compile(pattern)) for rule, pattern in RULES]

class ScanError(Exception):
    pass

def ordinary(path):
    stat = path.lstat()
    if path.is_symlink() or getattr(stat, 'st_file_attributes', 0) & 0x400:
        raise ScanError('reparse_or_symlink')
    return stat

def scan(data_dir, key):
    if key not in KEYS:
        raise ScanError('unexpected_cache_key')
    data_dir = Path(data_dir)
    ordinary(data_dir)
    if not data_dir.is_dir():
        raise ScanError('missing_restore_directory')
    entries = list(data_dir.iterdir())
    if not entries or any(p.name not in FILES for p in entries):
        raise ScanError('unexpected_or_empty_restore')
    metadata, findings, absent = [], [], []
    total = 0
    for name in FILES:
        path = data_dir / name
        if not path.exists():
            absent.append(name)
            continue
        stat = ordinary(path)
        if not path.is_file() or stat.st_size > FILE_LIMIT:
            raise ScanError('file_budget_or_type')
        total += stat.st_size
        if total > TOTAL_LIMIT:
            raise ScanError('total_budget')
        with path.open('rb') as file:
            raw = file.read(FILE_LIMIT + 1)
        if len(raw) != stat.st_size or len(raw) > FILE_LIMIT:
            raise ScanError('changed_file_or_budget')
        digest = hashlib.sha256(raw).hexdigest()
        phases = [('raw', raw.decode('utf-8', errors='replace'))]
        if name.endswith('.json'):
            try:
                decoded = json.loads(raw)
                phases.append(('decoded_json', json.dumps(decoded, ensure_ascii=False)))
            except Exception:
                raise ScanError('invalid_json') from None
        elif name == 'news.db':
            # Immutable is safe only with no WAL; scan the raw file as well as live SQL rows.
            if path.with_name(path.name + '-wal').exists():
                raise ScanError('wal_present')
            try:
                statements, used = [], 0
                with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
                    if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                        raise ScanError('sqlite_integrity')
                    for statement in db.iterdump():
                        used += len(statement.encode('utf-8'))
                        if used > FILE_LIMIT:
                            raise ScanError('sqlite_logical_budget')
                        statements.append(statement)
                phases.append(('logical_sqlite', '\n'.join(statements)))
            except ScanError:
                raise
            except Exception:
                raise ScanError('sqlite_read_failed') from None
        seen = set()
        for phase, text in phases:
            text = html.unescape(text)
            for rule, pattern in PATTERNS:
                for match in pattern.finditer(text):
                    location = (rule, phase, text[:match.start()].count('\n') + 1)
                    if location in seen:
                        continue
                    seen.add(location)
                    if len(findings) >= 10_000:
                        raise ScanError('finding_budget')
                    findings.append({'rule': rule, 'path': 'data/' + name,
                                     'phase': phase, 'line': location[2], 'sha256': digest})
        with path.open('rb') as file:
            after = file.read(FILE_LIMIT + 1)
        if len(after) > FILE_LIMIT or hashlib.sha256(after).hexdigest() != digest:
            raise ScanError('input_changed')
        metadata.append({'path': 'data/' + name, 'bytes': len(raw), 'sha256': digest,
                         'phases': [p for p, _ in phases]})
    return {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'key': key, 'status': 'scanned_with_findings' if findings else 'scanned_clear',
            'scope': 'all exact restored files; raw, decoded JSON, logical SQLite; eight privacy rules',
            'files_scanned': len(metadata), 'bytes_scanned_raw': total, 'files': metadata,
            'absent_requested_paths': absent, 'findings': findings,
            'finding_count': len(findings), 'raw_content_retained': False,
            'credential_validity_not_tested': True, 'public_release_clearance': False}

def self_check(root):
    with tempfile.TemporaryDirectory(prefix='cache-scanner-selfcheck-', dir=root) as temp:
        data = Path(temp) / 'data'
        data.mkdir()
        token = 'ghp_' + 'A' * 36  # Deliberate synthetic negative-test fixture, never a configured credential.
        (data / 'intel_state.json').write_text(json.dumps({'probe_evidence': token, 'name': 'Hearth POS'}), encoding='utf-8')
        db_path = data / 'news.db'
        with closing(sqlite3.connect(db_path)) as db:
            db.execute('CREATE TABLE articles(body TEXT)')
            db.execute('INSERT INTO articles VALUES (?)', ('http://' + '127.0.0.1:9000',))
            db.commit()
        before = hashlib.sha256(db_path.read_bytes()).hexdigest()
        report = scan(data, KEYS[0])
        rules = {f['rule'] for f in report['findings']}
        assert {'vendor_credential_shape', 'personal_project_material', 'operational_data_field', 'private_network_url'} <= rules
        assert any(f['phase'] == 'logical_sqlite' for f in report['findings'])
        assert token not in json.dumps(report)
        assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
        (data / 'unexpected.txt').write_text('test', encoding='utf-8')
        try:
            scan(data, KEYS[0])
        except ScanError:
            pass
        else:
            raise AssertionError('Unexpected restored member accepted')
        (data / 'unexpected.txt').unlink()
        (data / 'intel_state.json').write_text('{}', encoding='utf-8')
        db_path.unlink()
        assert scan(data, KEYS[1])['status'] == 'scanned_clear'
    print('cache scanner fixture self-check: PASS; redaction, decoded JSON, SQLite, input preservation, unexpected-member rejection, clear control')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--key', choices=KEYS)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.self_check:
        self_check(Path(__file__).parent)
    else:
        if not args.data_dir or not args.key or not args.output:
            parser.error('--data-dir, --key and --output required')
        assert not args.output.exists(), 'Refusing to overwrite prior evidence'
        assert args.data_dir.resolve() not in args.output.resolve().parents, 'Report must stay outside restored data'
        try:
            report = scan(args.data_dir, args.key)
        except Exception as error:
            report = {'schema_version': 1, 'key': args.key, 'status': 'blocked',
                      'error_class': type(error).__name__, 'public_release_clearance': False}
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: report[k] for k in ('key', 'status', 'files_scanned', 'finding_count') if k in report}))
        raise SystemExit(1 if report['status'] == 'blocked' else 0)
