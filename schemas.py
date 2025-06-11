# schemas.py
from pydantic import BaseModel, HttpUrl, constr


class UserCreate(BaseModel):
    username: constr(min_length=3)
    password: constr(min_length=5)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class URLBase(BaseModel):
    original_url: HttpUrl

class URLInfo(URLBase):
    short_url: str
    clicks: int

    class Config:
        from_attributes = True

