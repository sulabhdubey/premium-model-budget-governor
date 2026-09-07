"""Check explicit files/packages without echoing confidential content or paths."""
import argparse
import json
from pathlib import Path

from premium_model_budget_governor.publication import audit_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+')
    parser.add_argument('--terms-file', help='Private JSON list of phrases, kept outside version control')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    terms = json.loads(Path(args.terms_file).read_text(encoding='utf-8')) if args.terms_file else []
    result = audit_files(args.files, terms)
    output = json.dumps(result, indent=2) + '\n'
    if args.report:
        args.report.write_text(output, encoding='utf-8')
    print(output)
    return 0 if result['status'] == 'no_pattern_findings' else 1


if __name__ == '__main__':
    raise SystemExit(main())
