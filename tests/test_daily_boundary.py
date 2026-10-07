"""Daily navigation remains inside the existing standalone security gate."""
import pytest
from intel_sources.public_report import _standalone_html


def document(anchor, exists=True):
    section = f'<section id="{anchor}">Digest</section>' if exists else ''
    return ('<html><head><meta charset="UTF-8"></head><body>'
            f'<a href="#{anchor}">Read</a>{section}</body></html>')


@pytest.mark.parametrize('anchor', ['daily-digest', 'report-history'])
def test_owned_daily_navigation_is_allowed_with_existing_target(anchor):
    output = _standalone_html(document(anchor))
    assert f'href="#{anchor}"' in output
    assert "connect-src 'none'" in output
    assert "form-action 'none'" in output


@pytest.mark.parametrize('anchor', ['daily-digest', 'report-history'])
def test_owned_navigation_without_target_is_rejected(anchor):
    with pytest.raises(ValueError, match='unsafe link'):
        _standalone_html(document(anchor, exists=False))


def test_arbitrary_operational_anchor_is_not_authorized():
    with pytest.raises(ValueError, match='unsafe link'):
        _standalone_html(document('admin-settings'))
