from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class NewsItem(BaseModel):
    title: str
    content: str
    url: HttpUrl
    image_url: Optional[HttpUrl] = None
    source_name: str
    source_display_name: str # Add this line
    source_url: str
    published_date: Optional[datetime] = None
