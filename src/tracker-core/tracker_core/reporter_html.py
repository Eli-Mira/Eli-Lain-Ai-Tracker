"""HTML reporter using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class HTMLReporter:
    """Generate HTML reports from tracker data using templates."""
    
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"
    
    def __init__(self, theme: str = "default"):
        self.theme = theme
        self.env = Environment(
            loader=FileSystemLoader(str(self.TEMPLATE_DIR)),
            autoescape=True
        )
    
    def render(
        self,
        api_items: list[dict[str, Any]],
        news_items: list[dict[str, Any]] | None = None,
        tool_items: list[dict[str, Any]] | None = None,
        report_date: str | None = None,
        generated_at: str | None = None,
        persona_image_url: str | None = None
    ) -> str:
        from datetime import datetime, timezone
        
        if report_date is None:
            report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if generated_at is None:
            generated_at = datetime.now(timezone.utc).strftime("%H:%M UTC")
        if news_items is None:
            news_items = []
        if tool_items is None:
            tool_items = []
        
        template_name = f"report_template_{self.theme}.html" if self.theme != "default" else "report_template.html"
        
        try:
            template = self.env.get_template(template_name)
        except Exception:
            template = self.env.get_template("report_template.html")
        
        return template.render(
            report_date=report_date,
            generated_at=generated_at,
            api_items=api_items,
            news_items=news_items,
            tool_items=tool_items,
            persona_image_url=persona_image_url,
        )
    
    def save(
        self,
        output_path: Path | str,
        api_items: list[dict[str, Any]],
        news_items: list[dict[str, Any]] | None = None,
        tool_items: list[dict[str, Any]] | None = None,
        report_date: str | None = None,
        generated_at: str | None = None,
        persona_image_url: str | None = None,
    ) -> Path:
        html = self.render(
            api_items=api_items,
            news_items=news_items,
            tool_items=tool_items,
            report_date=report_date,
            generated_at=generated_at,
            persona_image_url=persona_image_url,
        )
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path


class LainReporter(HTMLReporter):
    def __init__(self):
        super().__init__(theme="lain")


class DefaultReporter(HTMLReporter):
    def __init__(self):
        super().__init__(theme="default")


def get_html_reporter(theme: str = "default") -> HTMLReporter:
    if theme == "lain":
        return LainReporter()
    return DefaultReporter()
