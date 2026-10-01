from pathlib import Path

path = Path("tests/test_report_delivery.py")
text = path.read_text(encoding="utf-8")

# The real Netlify deploy payload carries BOTH ssl_url (canonical published
# origin) and deploy_ssl_url (per-deploy alias). The stub only modelled the
# alias, so the readback silently lost its target. Mirror the real payload.
old_new = [
    ('''                return httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                               "deploy_ssl_url": URL.rstrip("/")})''',
     '''                return httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                               "ssl_url": URL.rstrip("/"),
                                               "deploy_ssl_url": ALIAS.rstrip("/")})'''),
    ('''        if host == "abc123--report-fixture.netlify.app":''',
     '''        if host in (ALIAS_HOST, URL_HOST):'''),
    ('''                     and httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                                    "deploy_ssl_url": "https://evil.example.com/"}))''',
     '''                     and httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                                    "ssl_url": "https://evil.example.com/"}))'''),
]
for old, new in old_new:
    assert text.count(old) == 1, old[:70]
    text = text.replace(old, new)

# Declare the alias host next to the existing URL constant.
anchor = 'URL = "https://abc123--report-fixture.netlify.app"'
if anchor in text:
    text = text.replace(
        anchor,
        'URL = "https://report-fixture.netlify.app"\n'
        'URL_HOST = "report-fixture.netlify.app"\n'
        '# Netlify answers 401 for this per-deploy alias on a team site; the\n'
        '# canonical ssl_url above is what is published and must be read back.\n'
        'ALIAS = "https://abc123--report-fixture.netlify.app"\n'
        'ALIAS_HOST = "abc123--report-fixture.netlify.app"', 1)
else:
    import re
    match = re.search(r'^URL = .*$', text, re.M)
    assert match, "URL constant not found"
    text = text[:match.start()] + (
        'URL = "https://report-fixture.netlify.app"\n'
        'URL_HOST = "report-fixture.netlify.app"\n'
        '# Netlify answers 401 for this per-deploy alias on a team site; the\n'
        '# canonical ssl_url above is what is published and must be read back.\n'
        'ALIAS = "https://abc123--report-fixture.netlify.app"\n'
        'ALIAS_HOST = "abc123--report-fixture.netlify.app"') + text[match.end():]

path.write_text(text, encoding="utf-8")
print("fixtures now model both ssl_url and deploy_ssl_url")