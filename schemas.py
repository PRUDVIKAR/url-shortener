# schemas.py
from pydantic import BaseModel

class URLBase(BaseModel):
    original_url: str

class URLInfo(URLBase):
    short_url: str
    clicks: int

    class Config:
        from_attributes = True

