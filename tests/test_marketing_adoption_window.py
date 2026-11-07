import json
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/mirrors-marketing/marketing-reverse-engineer-marketing/scripts/teardown.mjs'


@pytest.mark.parametrize('months, now, first, last, buckets', [
    (24, '2026-11-06T12:00:00Z', '2024-12-01', '2026-11-05', 24),
    (1, '2026-11-06T12:00:00Z', '2026-11-01', '2026-11-05', 1),
    (3, '2026-01-05T12:00:00Z', '2025-11-01', '2026-01-04', 3),
    (2, '2024-03-05T12:00:00Z', '2024-02-01', '2024-03-04', 2),
])
def test_npm_adoption_covers_requested_calendar_months(months, now, first, last, buckets):
    program = f'import {{ npmRanges }} from {json.dumps(SCRIPT.as_uri())}; console.log(JSON.stringify(npmRanges(Number(process.argv[1]), new Date(process.argv[2]))));'
    result = subprocess.run(['node', '--input-type=module', '--eval', program, str(months), now], check=True, capture_output=True, text=True)
    ranges = json.loads(result.stdout)
    assert ranges[0]['from'] == first
    assert ranges[-1]['to'] == last
    days = []
    for item in ranges:
        start, end = date.fromisoformat(item['from']), date.fromisoformat(item['to'])
        assert 0 <= (end - start).days < 365
        if days:
            assert start == days[-1] + timedelta(days=1)
        days.extend(start + timedelta(days=offset) for offset in range((end - start).days + 1))
    assert len({day.strftime('%Y-%m') for day in days}) == buckets


def test_current_month_has_no_completed_days_on_its_first_day():
    program = f'import {{ npmRanges }} from {json.dumps(SCRIPT.as_uri())}; console.log(JSON.stringify(npmRanges(1, new Date("2026-11-01T12:00:00Z"))));'
    result = subprocess.run(['node', '--input-type=module', '--eval', program], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == []


def test_curated_check_rejects_a_lost_reviewed_correction(tmp_path):
    for name in ['scripts/sync-curated-mirrors.mjs', 'config/mirror-sources.json', '.claude-plugin/marketplace.json']:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    shutil.copytree(ROOT / 'skills/mirrors-marketing', tmp_path / 'skills/mirrors-marketing')
    mirrored = tmp_path / SCRIPT.relative_to(ROOT)
    mirrored.write_text(mirrored.read_text().replace('now.getUTCMonth() - (months - 1), 1', 'now.getUTCMonth() - months, 1'))
    result = subprocess.run(['node', str(tmp_path / 'scripts/sync-curated-mirrors.mjs'), '--check', '--family', 'marketing'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'reviewed patch missing or modified' in result.stderr
