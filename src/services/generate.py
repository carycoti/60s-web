from jinja2 import Environment, FileSystemLoader
from typing import List
from src.models.news_item import NewsItem
from datetime import datetime

from typing import List, Dict

def generate_briefing(items: Dict[str, List[NewsItem]], template_path: str = "src/templates") -> str:
    """Generates the HTML briefing from a list of news items."""
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("briefing.html")

    today = datetime.now().strftime("%Y-%m-%d")
    title = f"每日简报 - {today}"

    return template.render(
        title=title,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        items=items
    )
