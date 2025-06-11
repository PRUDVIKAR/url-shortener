import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import Base, SessionLocal, engine


SECRET_KEY = "change_this_secret"  # In production use env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


def get_current_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not crud.get_user_by_username(db, "admin"):
        crud.create_user(db, "admin", "admin", is_admin=True)
    db.close()


@app.get("/", response_class=HTMLResponse)
def serve_homepage():
    with open(os.path.join("static", "index.html")) as f:
        return f.read()


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/shorten", response_model=schemas.URLInfo)
def create_short_url(payload: schemas.URLBase, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_url = crud.get_or_create_short_url(db, original_url=payload.original_url, owner_id=current_user.id)
    short_url = f"{request.base_url}{db_url.short_code}"
    return {
        "original_url": db_url.original_url,
        "short_url": short_url,
        "clicks": db_url.clicks,
    }


@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    db_url = crud.get_url_by_code(db, short_code)
    if db_url:
        crud.log_click(db, db_url)
        return RedirectResponse(url=db_url.original_url)
    raise HTTPException(status_code=404, detail="URL not found")


@app.get("/analytics/{short_code}")
def analytics(short_code: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_url = crud.get_url_by_code(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    if db_url.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    return {
        "original_url": db_url.original_url,
        "short_code": db_url.short_code,
        "clicks": db_url.clicks,
        "created_at": db_url.created_at,
    }


@app.get("/admin/analytics")
def all_analytics(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin)):
    urls = db.query(models.URL).all()
    return [
        {
            "original_url": u.original_url,
            "short_code": u.short_code,
            "clicks": u.clicks,
            "created_at": u.created_at,
        }
        for u in urls
    ]

