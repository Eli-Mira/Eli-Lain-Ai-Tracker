"""Real cockpit journeys; synthetic callbacks, no external acquisition."""
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright
from intel_sources import dashboard
from intel_sources.settings import save_settings


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.environ.get('PLAYWRIGHT_EXECUTABLE_PATH'):
            options['executable_path'] = os.environ['PLAYWRIGHT_EXECUTABLE_PATH']
        with pw.chromium.launch(**options) as instance:
            yield instance


@pytest.fixture
def cockpit(tmp_path, monkeypatch):
    owned = []
    entered, release = threading.Event(), threading.Event()
    state = {'fail': False, 'calls': 0}

    def tracked_thread(*args, **kwargs):
        thread = threading.Thread(*args, **kwargs)
        owned.append(thread)
        return thread

    monkeypatch.setattr(dashboard, 'threading', SimpleNamespace(Thread=tracked_thread, Lock=threading.Lock))
    with dashboard._scan_state['lock']:
        dashboard._scan_state.update(running=False, status='idle', last_error=None, last_report=None)
    path = tmp_path / 'settings.json'
    settings = {
        'schema_version': 1,
        'sources': [{'id': 'synthetic-source', 'name': 'Synthetic source',
                     'adapter': 'rss', 'enabled': False,
                     'url': 'https://example.org/synthetic.xml'}],
        'topics': ['Synthetic topic'], 'priorities': {'mcp': 3}, 'categories': ['mcp'],
        'max_items': 5, 'max_age_days': 7, 'min_score': 60,
        'schedule': {'timezone': 'UTC', 'hour': 10, 'minute': 0}}
    initial = save_settings(path, settings)

    history = tmp_path / 'history'
    history.mkdir()
    (history / 'history.jsonl').write_text(json.dumps({'report_date': '2026-01-01',
        'generated_at': '2026-01-01T10:00:00+00:00', 'counts': {'selected': 1}}) + '\n', encoding='utf-8')
    public = tmp_path / 'public'
    public.mkdir()
    (public / 'index.html').write_text('<!DOCTYPE html><title>Synthetic report</title><h1>Synthetic report</h1>', encoding='utf-8')

    csrf_token = dashboard._issue_csrf_token()

    def scan(settings):
        state['calls'] += 1
        state['received'] = settings
        entered.set()
        assert release.wait(10), 'Synthetic callback was not released'
        if state['fail']:
            raise RuntimeError('SYNTHETIC_CALLBACK_PRIVATE_CANARY')
        return {'report_date': '2026-01-01'}

    server = dashboard.serve_dashboard(path, history, scan, port=0,
        templates_dir=Path(__file__).resolve().parents[1] / 'src/templates')
    result = SimpleNamespace(base=f'http://127.0.0.1:{server.server_port}', entered=entered, release=release,
                             state=state, path=path, initial=initial, csrf_token=csrf_token)
    try:
        yield result
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        for thread in owned:
            thread.join(timeout=5)
            assert not thread.is_alive(), 'Owned cockpit thread survived teardown'
        with dashboard._scan_state['lock']:
            dashboard._scan_state.update(running=False, status='idle', last_error=None, last_report=None)
        with dashboard._csrf_lock:
            dashboard._csrf_tokens.clear()


@contextmanager
def page_for(browser, cockpit, width=1200):
    context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
    errors, external = [], []

    def admit(route):
        if urlsplit(route.request.url).netloc == urlsplit(cockpit.base).netloc:
            route.continue_()
        else:
            external.append(route.request.url)
            route.abort()

    context.route('**/*', admit)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
    try:
        response = page.goto(cockpit.base + '/', wait_until='networkidle')
        assert response.status == 200, 'Ordinary browser navigation must load the cockpit'
        expect(page.get_by_role('heading', name='EliLain Intelligence Cockpit')).to_be_visible()
        yield page
        assert not errors, errors
        assert not external, external
    finally:
        context.close()


def test_cockpit_repeated_settings_save_preserves_full_policy(browser, cockpit):
    with page_for(browser, cockpit) as page:
        expect(page.locator('#max_items')).to_have_value('5')
        for value in ['7', '8']:
            page.locator('#max_items').fill(value)
            with page.expect_response(lambda r: r.url.endswith('/api/settings') and r.request.method == 'POST') as saved:
                page.get_by_role('button', name='Save Settings', exact=True).click()
            assert saved.value.status == 200, saved.value.text()
            assert json.loads(cockpit.path.read_bytes()) == {**cockpit.initial, 'max_items': int(value)}
            expect(page.locator('#max_items')).to_have_value(value)
        page.reload(wait_until='networkidle')
        expect(page.locator('#max_items')).to_have_value('8')
        assert json.loads(cockpit.path.read_bytes()) == {**cockpit.initial, 'max_items': 8}


@pytest.mark.parametrize('fail', [False, True])
def test_cockpit_scan_loading_completion_and_retry(browser, cockpit, fail):
    cockpit.state['fail'] = fail
    with page_for(browser, cockpit) as page:
        expect(page.locator('#history-list')).to_contain_text('report_2026-01-01')
        for attempt in range(2):
            cockpit.entered.clear()
            cockpit.release.clear()
            with page.expect_response(lambda r: r.url.endswith('/api/scan') and r.request.method == 'POST') as started:
                page.get_by_role('button', name='Run Scan', exact=True).click()
            assert started.value.status == 200, started.value.text()
            assert cockpit.entered.wait(3), 'Real callback thread never entered'
            expect(page.locator('#scan-btn')).to_be_disabled()
            expect(page.locator('#status-spinner')).to_be_visible(timeout=6000)
            cockpit.release.set()
            expect(page.locator('#status-text')).to_have_text('Failed' if fail else 'Completed', timeout=8000)
            expect(page.locator('#status-spinner')).to_be_hidden()
            expect(page.locator('#scan-btn')).to_be_enabled()
            assert cockpit.state['calls'] == attempt + 1
            assert cockpit.state['received'] == cockpit.initial
            if fail:
                assert 'SYNTHETIC_CALLBACK_PRIVATE_CANARY' not in page.content()
                expect(page.locator('#last-error')).not_to_have_text('None')


def test_cockpit_history_link_opens_served_report(browser, cockpit):
    with page_for(browser, cockpit) as page:
        page.get_by_role('link', name='View', exact=True).click()
        expect(page).to_have_url(cockpit.base + '/reports/report_2026-01-01.html')
        expect(page.get_by_role('heading', name='Synthetic report', exact=True)).to_be_visible()


@pytest.mark.parametrize('width', [320, 390, 1440])
def test_cockpit_reflows_and_keyboard_focus_is_visible(browser, cockpit, width):
    with page_for(browser, cockpit, width) as page:
        page.keyboard.press('Tab')
        expect(page.locator('#scan-btn')).to_be_focused()
        focus = page.locator('#scan-btn').evaluate('(e)=>({style:getComputedStyle(e).outlineStyle,width:parseFloat(getComputedStyle(e).outlineWidth)})')
        assert focus['style'] != 'none' and focus['width'] > 0, focus
        page.evaluate("document.body.style.zoom='2'")
        page.screenshot()
        assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1')


@pytest.mark.parametrize('headers', [
    {'Origin': 'http://evil.example'}, {'Host': 'evil.example'},
    {'Sec-Fetch-Site': 'cross-site'}, {'Origin': 'null'}])
def test_cockpit_rejects_cross_origin_get(browser, cockpit, headers):
    context = browser.new_context()
    try:
        result = context.request.get(cockpit.base + '/api/settings', headers=headers)
        assert result.status == 403
    finally:
        context.close()
