from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from src.services.fetch import fetch_news
from src.services.generate import generate_briefing
from collections import defaultdict

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/", response_class=Response)
def read_root():
    """Fetches news, groups them by source, generates a briefing, and returns it as HTML."""
    news_items = fetch_news()
    
    # Group items by source
    grouped_items = defaultdict(list)
    for item in news_items:
        grouped_items[item.source_display_name].append(item)
    
    html_content = generate_briefing(grouped_items)
    return Response(content=html_content, media_type="text/html")
