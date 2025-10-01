import pytest
from unittest.mock import patch, MagicMock
from src.services.fetch import _fetch_from_rss, _fetch_from_api

# Mock data for RSS feed
@pytest.fixture
def mock_rss_feed():
    feed = MagicMock()
    feed.entries = [
        {
            'title': 'RSS Title 1',
            'summary': 'RSS Summary 1',
            'link': 'http://test.com/rss1',
            'media_content': [{'url': 'http://test.com/img1.jpg'}]
        }
    ]
    feed.feed.title = 'RSS Source'
    return feed

# Mock data for API response
@pytest.fixture
def mock_api_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        'articles': [
            {
                'title': 'API Title 1',
                'description': 'API Description 1',
                'url': 'http://test.com/api1',
                'urlToImage': 'http://test.com/img2.jpg',
                'source': {'name': 'API Source'}
            }
        ]
    }
    return response

@patch('feedparser.parse')
def test_fetch_from_rss(mock_parse, mock_rss_feed):
    mock_parse.return_value = mock_rss_feed
    items = _fetch_from_rss({'type': 'RSS', 'url': 'http://test.com/rss'})
    assert len(items) == 1
    assert items[0].title == 'RSS Title 1'
    assert items[0].source_name == 'RSS Source'

@patch('requests.get')
def test_fetch_from_api(mock_get, mock_api_response):
    mock_get.return_value = mock_api_response
    items = _fetch_from_api({'type': 'API', 'url': 'http://test.com/api', 'auth_key': 'key'})
    assert len(items) == 1
    assert items[0].title == 'API Title 1'
    assert items[0].source_name == 'API Source'

def test_fetch_invalid_source_type():
    # This test is for the main fetch_news function which is not tested here directly
    # but we can test the private functions for robustness
    items = _fetch_from_rss({'type': 'RSS', 'url': None}) # feedparser handles this gracefully
    assert len(items) == 0
