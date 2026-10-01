from pathlib import Path
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_scheduled_workflow_actually_runs_discovery_and_restores_history():
    workflow = yaml.safe_load((ROOT / '.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8'))
    steps = workflow['jobs']['run-elilain-audit']['steps']
    commands = '\n'.join(s.get('run', '') for s in steps)
    assert 'python main.py audit --theme lain' in commands
    cache_steps = [s for s in steps if s.get('uses', '').startswith('actions/cache@')]
    assert any('data/intel_state.json' in s['with']['path'] for s in cache_steps)
    assert workflow['permissions']['contents'] == 'read'


def test_declared_dependencies_and_ci_prepare_browser_tests():
    project = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']
    assert any(d.startswith('beautifulsoup4') for d in project['dependencies'])
    assert any(d.startswith('playwright') for d in project['optional-dependencies']['dev'])
    workflow = yaml.safe_load((ROOT/'.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8'))
    steps = workflow['jobs']['run-elilain-audit']['steps']
    commands = '\n'.join(s.get('run', '') for s in steps)
    assert 'python -m playwright install --with-deps chromium' in commands
    cache_paths = '\n'.join(s['with']['path'] for s in steps if s.get('uses', '').startswith('actions/cache@'))
    assert 'data/provider_state.json' in cache_paths
    assert 'data/provider_changes.json' in cache_paths
    schedules = []
    for path in (ROOT/'.github/workflows').glob('*.yml'):
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        if (data.get('on') or data.get(True) or {}).get('schedule'):
            schedules.append(path)
    assert len(schedules) == 1
