from pathlib import Path
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_scheduled_workflow_actually_runs_discovery_and_restores_history():
    workflow = yaml.safe_load((ROOT / '.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8'))
    steps = workflow['jobs']['run-elilain-audit']['steps']
    commands = '\n'.join(s.get('run', '') for s in steps)
    assert 'python main.py audit --theme lain' in commands
    cache_steps = [s for s in steps if s.get('uses', '').startswith(('actions/cache@', 'actions/cache/restore@'))]
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
    cache_paths = '\n'.join(s['with']['path'] for s in steps if s.get('uses', '').startswith(('actions/cache@', 'actions/cache/restore@')))
    assert 'data/provider_state.json' in cache_paths
    assert 'data/provider_changes.json' in cache_paths
    schedules = []
    for path in (ROOT/'.github/workflows').glob('*.yml'):
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        if (data.get('on') or data.get(True) or {}).get('schedule'):
            schedules.append(path)
    assert len(schedules) == 1


def test_publish_step_is_gated_without_using_secrets_in_step_if():
    # `secrets` is not available in a step-level `if`; GitHub rejects the whole
    # workflow file for it. Gate on a repository variable instead.
    text = (ROOT/'.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8')
    workflow = yaml.safe_load(text)
    steps = workflow['jobs']['run-elilain-audit']['steps']
    publish = [s for s in steps if 'main.py publish' in s.get('run', '')]
    assert len(publish) == 1, 'exactly one publish step is expected'
    condition = publish[0]['if']
    assert 'secrets.' not in condition, f'secrets context is invalid in a step if: {condition}'
    assert 'vars.PUBLISH_ENABLED' in condition
    # Secrets still reach the process through env, never through argv or interpolation.
    env = publish[0]['env']
    for name in ('NETLIFY_AUTH_TOKEN', 'NETLIFY_SITE_ID', 'TELEGRAM_BOT_TOKEN',
                 'TELEGRAM_CHAT_ID', 'DISCORD_BOT_TOKEN', 'DISCORD_CHANNEL_ID'):
        assert env[name] == '${{ secrets.%s }}' % name
    assert 'secrets.' not in publish[0]['run']
    # No untrusted event text interpolated into any run block.
    for step in steps:
        for suspect in ('github.event.issue', 'github.event.pull_request',
                        'github.event.comment', 'github.head_ref', 'github.event.discussion'):
            assert suspect not in step.get('run', '')


def test_public_export_step_runs_before_any_publish_or_upload():
    workflow = yaml.safe_load((ROOT/'.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8'))
    steps = workflow['jobs']['run-elilain-audit']['steps']

    export_index = next(i for i, s in enumerate(steps) if 'main.py export-public' in s.get('run', ''))
    publish_index = next(i for i, s in enumerate(steps) if 'main.py publish' in s.get('run', ''))
    public_upload = next(i for i, s in enumerate(steps)
                         if (s.get('with', {}).get('path') or '').strip() == 'public/index.html')
    assert export_index < publish_index
    assert export_index < public_upload
    assert steps[public_upload]['with']['name'].startswith('elain-public')


def test_workflow_references_no_deleted_email_secrets():
    """The email channel was removed; the workflow must not request its secrets.

    Deleting EMAIL_* secrets while the workflow still injects them leaves
    empty-string credentials in the environment, which is how a removed
    channel turns into a recurring authentication error instead of simply
    disappearing.
    """
    text = (ROOT/'.github/workflows/news-tracker-daily.yml').read_text(encoding='utf-8')
    workflow = yaml.safe_load(text)
    steps = workflow['jobs']['run-elilain-audit']['steps']
    env_names = set()
    for step in steps:
        env_names.update((step.get('env') or {}).keys())
    removed = {'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_TO'}
    assert not (env_names & removed), f"workflow still injects removed secrets: {env_names & removed}"
    assert 'secrets.EMAIL_' not in text

    # The channel list comes from an encrypted secret, not the plaintext variable.
    audit = next(s for s in steps if 'main.py audit' in s.get('run', ''))
    assert audit['env']['NOTIFICATION_CHANNEL'] == '${{ secrets.NOTIFICATION_CHANNEL }}'
    assert 'NOTIFICATION_CHANNEL' not in env_names - {'NOTIFICATION_CHANNEL'}
