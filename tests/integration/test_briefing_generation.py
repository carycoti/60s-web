import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch

client = TestClient(app)

@patch('src.main.fetch_news')
def test_read_root_integration(mock_fetch_news):
    # Mock the fetch_news function to return some sample data
    from src.models.news_item import NewsItem
    from datetime import datetime
    mock_fetch_news.return_value = [
        NewsItem(
            title='Integration Test Title',
            content='Integration Test Content',
            url='http://integration.test/1',
            source_name='Integration Source',
            published_date=datetime.now()
        )
    ]

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/html; charset=utf-8'
    html = response.text
    assert '<h1>Daily News Briefing' in html
    assert '<h2><a href="http://integration.test/1"' in html
    assert '>Integration Test Title</a></h2>' in html
