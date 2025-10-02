import json
import re
import time
import requests
import feedparser
from typing import List, Dict
from datetime import datetime
from src.models.news_item import NewsItem
from pydantic import ValidationError
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_news(config_path: str = "config.json") -> List[NewsItem]:
    """Fetches news items from sources defined in the config file and de-duplicates them."""
    print(f"--- Fetching news from {config_path} ---")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found.")
        return []

    all_items = []
    for source in config.get('sources', []):
        print(f"Processing source: {source.get('url')}")
        if source.get('type') == 'RSS':
            all_items.extend(_fetch_from_rss(source))
        elif source.get('type') == 'API':
            all_items.extend(_fetch_from_api(source))
    
    print(f"--- Fetched {len(all_items)} items in total before de-duplication. ---")
    
    unique_items = {}
    for item in all_items:
        title = item.title.strip()
        if title not in unique_items or len(item.content) > len(unique_items[title].content):
            unique_items[title] = item
            
    deduplicated_list = list(unique_items.values())
    print(f"--- Returning {len(deduplicated_list)} unique items. ---")
    
    return deduplicated_list

def _fetch_from_rss(source: Dict) -> List[NewsItem]:
    """Fetches news items from an RSS feed."""
    feed = feedparser.parse(source.get('url'))
    source_name = feed.feed.get('title', 'Unknown RSS')
    print(f"Found {len(feed.entries)} entries for {source_name}")
    items = []
    for entry in feed.entries[:50]:
        image_url = None

        source_url = source.get('url', '')

        # Source-specific logic
        if 'tmtpost.com' in source_url:
            content_html = entry.get('content', [{}])[0].get('value', '')
            if content_html:
                soup = BeautifulSoup(content_html, 'html.parser')
                image_tag = soup.find('img')
                if image_tag and image_tag.get('src'):
                    image_url = image_tag.get('src')
        elif 'sspai.com' in source_url or 'cankaoxiaoxi.com' in source_url:
            summary_html = entry.get('summary', '')
            if summary_html:
                soup = BeautifulSoup(summary_html, 'html.parser')
                image_tag = soup.find('img')
                if image_tag and image_tag.get('src'):
                    image_url = image_tag.get('src')
        else: # Generic fallback
            if 'media_content' in entry and entry.media_content:
                image_url = entry.media_content[0].get('url')
            
            if not image_url:
                html_to_search = entry.get('summary', '')
                if not html_to_search:
                    content_list = entry.get('content', [])
                    if content_list:
                        html_to_search = content_list[0].get('value', '')

                if html_to_search:
                    soup = BeautifulSoup(html_to_search, 'html.parser')
                    image_tag = soup.find('img')
                    if image_tag and image_tag.get('src'):
                        image_url = image_tag.get('src')

        # Convert relative image URLs to absolute
        if image_url and not image_url.startswith(('http://', 'https://')):
            try:
                base_url = entry.link
                image_url = urljoin(base_url, image_url)
            except Exception as e:
                print(f"Error converting relative URL to absolute: {e}")
                image_url = None

        summary_html = entry.get('summary', 'No Content')
        soup = BeautifulSoup(summary_html, 'html.parser')
        
        # Get text from all paragraphs and join them with a newline
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        content = '\n'.join(paragraphs)
        
        # If there are no p tags, just get all the text
        if not content:
            content = soup.get_text()

        published_parsed = entry.get('published_parsed')
        published_date = datetime.fromtimestamp(time.mktime(published_parsed)) if published_parsed else None

        items.append(NewsItem(
            title=entry.get('title', 'No Title'),
            content=content,
            url=entry.get('link'),
            image_url=image_url,
            source_name=source_name,
            source_display_name=source.get('name', source_name),
            source_url=source.get('url'),
            published_date=published_date
        ))
    return items

def _fetch_from_api(source: Dict) -> List[NewsItem]:
    """Fetches news items from a news API, handling different JSON structures."""
    headers = {}
    if 'auth_key' in source:
        headers['Authorization'] = f"Bearer {source['auth_key']}"
    
    try:
        response = requests.get(source.get('url'), headers=headers)
        response.raise_for_status()
        print(f"Successfully fetched from {source.get('url')}")
        
        data = response.json()
        main_data = data.get('data')

        if main_data is None:
            print("No 'data' key found in response.")
            return []

        news_list = []
        if isinstance(main_data, dict):
            news_list = main_data.get('news', [])
        elif isinstance(main_data, list):
            news_list = main_data
        
        news_list = news_list[:50]
        print(f"Found {len(news_list)} items to process.")

        items = []
        for item in news_list:
            try:
                if isinstance(item, str):
                    items.append(NewsItem(
                        title=item,
                        content='',
                        url=main_data.get('link', 'http://example.com') if isinstance(main_data, dict) else 'http://example.com',
                        source_name=source.get('url').split('/')[2],
                        source_display_name=source.get('name', source.get('url').split('/')[2]),
                        source_url=source.get('url')
                    ))
                elif isinstance(item, dict):
                    content = item.get('description') or item.get('desc') or ''
                    url = item.get('url') or item.get('link') or 'http://example.com'
                    image_url = item.get('urlToImage') or item.get('cover')

                    items.append(NewsItem(
                        title=item.get('title', 'No Title'),
                        content=content,
                        url=url,
                        image_url=image_url,
                        source_name=item.get('source', {}).get('name', source.get('url').split('/')[2]),
                        source_display_name=source.get('name', item.get('source', {}).get('name', source.get('url').split('/')[2])),
                        source_url=source.get('url'),
                        published_date=item.get('publishedAt')
                    ))
            except ValidationError as e:
                print(f"Validation error for item: {item}. Error: {e}")
        return items

    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error processing {source.get('url')}: {e}")
        return []