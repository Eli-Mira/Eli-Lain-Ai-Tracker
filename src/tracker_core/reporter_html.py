"""HTML reporter using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class HTMLReporter:
    """Generate HTML reports from tracker data using templates."""
    
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"
    
    def __init__(self, theme: str = "default"):
        """Initialize reporter with theme.
        
        Args:
            theme: "default" or "lain"
        """
        self.theme = theme
        self.env = Environment(
            loader=FileSystemLoader(str(self.TEMPLATE_DIR)),
            autoescape=True
        )
    
    def render(
        self,
        api_items: list[dict[str, Any]],
        news_items: list[dict[str, Any]] | None = None,
        report_date: str | None = None,
        generated_at: str | None = None,
        persona_image_url: str | None = None
    ) -> str:
        """Render HTML report from data."""
        from datetime import datetime, timezone
        
        if report_date is None:
            report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if generated_at is None:
            generated_at = datetime.now(timezone.utc).strftime("%H:%M UTC")
        if news_items is None:
            news_items = []
        
        template_name = f"report_template_{self.theme}.html" if self.theme != "default" else "report_template.html"
        
        try:
            template = self.env.get_template(template_name)
        except Exception:
            # Fallback to default template
            template = self.env.get_template("report_template.html")
        
        return template.render(
            report_date=report_date,
            generated_at=generated_at,
            api_items=api_items,
            news_items=news_items,
            persona_image_url=persona_image_url
        )
    
    def save(
        self,
        output_path: Path | str,
        api_items: list[dict[str, Any]],
        news_items: list[dict[str, Any]] | None = None,
        report_date: str | None = None,
        generated_at: str | None = None,
        persona_image_url: str | None = None
    ) -> Path:
        """Render and save report to file."""
        html = self.render(
            api_items=api_items,
            news_items=news_items,
            report_date=report_date,
            generated_at=generated_at,
            persona_image_url=persona_image_url
        )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        
        return output_path


class LainReporter(HTMLReporter):
    """Report with lain theme."""
    
    def __init__(self):
        super().__init__(theme="lain")


class DefaultReporter(HTMLReporter):
    """Report with default theme."""
    
    def __init__(self):
        super().__init__(theme="default")


def get_html_reporter(theme: str = "default") -> HTMLReporter:
    """Factory function to get HTML reporter."""
    if theme == "lain":
        return LainReporter()
    return DefaultReporter()
