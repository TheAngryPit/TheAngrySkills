#!/usr/bin/env python3
"""Report upstream drift without modifying adapted skills or accepted baselines."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('skills/core/ask-pit', 'skills/engineering/writing-for-astra')
UPSTREAM = 'https://github.com/mattpocock/skills.git'


def snapshot(checkout, source_path):
    source = checkout / source_path
    result = {}
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Upstream symlink requires manual inspection')
        if path.is_file():
            result[str(path.relative_to(source))] = hashlib.sha256(path.read_bytes()).hexdigest()
    result['LICENSE'] = hashlib.sha256((checkout / 'LICENSE').read_bytes()).hexdigest()
    return result


def changed_files(baseline, current):
    return sorted(k for k in baseline.keys() | current.keys() if baseline.get(k) != current.get(k))


def check(checkout, root=ROOT):
    head = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    reports = []
    for package in PACKAGES:
        baseline = json.loads((root / package / 'UPSTREAM.json').read_text())
        changed = changed_files(baseline['upstream_sha256'], snapshot(checkout, baseline['source_path']))
        if changed:
            reports.append(dict(skill=Path(package).name, package=package, source_path=baseline['source_path'],
                                reviewed=baseline['commit'], latest=head, changed=changed))
    return reports


def notify(report):
    title = 'Upstream review: ' + report['skill']
    marker = '<!-- adapted-skill-upstream:' + report['skill'] + ' -->'
    body = (marker + '\nUpstream changed. Our skill and accepted baseline remain untouched.\n\n'
            + 'Compare: https://github.com/mattpocock/skills/compare/' + report['reviewed'] + '...' + report['latest']
            + '\n\nSource directory: `' + report['source_path'] + '`\n\nChanged paths (upstream data):\n'
            + '\n'.join('- `' + name.replace('`', '') + '`' for name in report['changed'])
            + '\n\nRead the adjacent [' + report['skill'] + ' provenance](' + report['package'] + '/PROVENANCE.md) and '
            + '[Astra guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).\n\n'
            + 'Review the diff and retain the documented adaptations. After approval, update the skill as needed '
            + 'and record the reviewed source commit/hashes in UPSTREAM.json, including intentionally skipped changes. '
            + 'Closing this issue alone does not acknowledge a new baseline. No automatic merge or skill rewrite.\n')
    # Link to repo files from an issue, not a relative issue URL.
    body = body.replace('](' + report['package'], '](https://github.com/' + os.environ['GITHUB_REPOSITORY'] + '/blob/main/' + report['package'])
    issues = json.loads(subprocess.check_output(['gh', 'issue', 'list', '--state', 'open', '--search', title + ' in:title', '--json', 'number,title,body'], text=True))
    issue = next((i for i in issues if i['title'] == title and marker in i['body']), None)
    if issue and issue['body'] == body:
        return
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as f:
        f.write(body); f.flush()
        cmd = ['gh', 'issue', 'edit', str(issue['number'])] if issue else ['gh', 'issue', 'create', '--title', title]
        subprocess.run(cmd + ['--body-file', f.name], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path)
    parser.add_argument('--notify', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        checkout = args.upstream or Path(temp) / 'source'
        if not args.upstream:
            subprocess.run(['git', 'clone', '--depth', '1', '--branch', 'main', UPSTREAM, str(checkout)], check=True)
        reports = check(checkout)
        print(json.dumps(reports, indent=2))
        if args.notify:
            for report in reports:
                notify(report)


if __name__ == '__main__':
    main()
