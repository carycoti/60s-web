import pytest
from src.models.news_item import NewsItem
from src.services.generate import generate_briefing
from datetime import datetime

@pytest.fixture
def sample_news_items():
    return [
        NewsItem(
            title='Test Title 1',
            content='Test Content 1',
            url='http://test.com/1',
            source_name='Test Source 1',
            published_date=datetime.now()
        )
    ]

def test_generate_briefing(sample_news_items):
    html = generate_briefing(sample_news_items, template_path="src/templates")
    today = datetime.now().strftime("%Y-%m-%d")
    assert f'<h1>Daily News Briefing - {today}</h1>' in html
    assert '<h2><a href="http://test.com/1"' in html
    assert '>Test Title 1</a></h2>' in html
    assert '<p>Test Content 1</p>' in html
