# crud.py
import random
import string
from sqlalchemy.orm import Session
from models import URL, User, ClickLog
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_url_by_code(db: Session, code: str):
    return db.query(URL).filter(URL.short_code == code).first()

def get_or_create_short_url(db: Session, original_url: str, owner_id: int | None = None) -> URL:
    existing = db.query(URL).filter(URL.original_url == original_url, URL.owner_id == owner_id).first()
    if existing:
        return existing

    # Generate a unique 6-character code
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not db.query(URL).filter(URL.short_code == code).first():
            break

    new_url = URL(original_url=original_url, short_code=code, owner_id=owner_id)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return new_url


def log_click(db: Session, url: URL):
    db.add(ClickLog(url_id=url.id))
    url.clicks += 1
    db.commit()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str, is_admin: bool = False) -> User:
    hashed_pw = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_pw, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


