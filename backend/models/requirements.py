from beanie import Document
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import HttpUrl

class RequirementsDocument(Document):
    request_id: str
    title: str
    requirements: Dict[str, Any]
    created_at: datetime = datetime.utcnow()
    status: str = "completed"
    url: Optional[HttpUrl] = None

    class Settings:
        name = "requirements"
        indexes = [
            "url"  # Index on URL for faster lookups
        ]