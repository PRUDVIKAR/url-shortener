# crud.py
import random
import string
from sqlalchemy.orm import Session
from models import URL

def get_url_by_code(db: Session, code: str):
    return db.query(URL).filter(URL.short_code == code).first()

def get_or_create_short_url(db: Session, original_url: str) -> URL:
    existing = db.query(URL).filter(URL.original_url == original_url).first()
    if existing:
        return existing

    # Generate a unique 6-character code
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not db.query(URL).filter(URL.short_code == code).first():
            break

    new_url = URL(original_url=original_url, short_code=code)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return new_url


