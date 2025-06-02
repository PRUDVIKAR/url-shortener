from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_homepage():
    with open(os.path.join("static", "index.html")) as f:
        return f.read()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/shorten", response_model=schemas.URLInfo)
def create_short_url(payload: schemas.URLBase, db: Session = Depends(get_db)):
    db_url = crud.get_or_create_short_url(db, original_url=payload.original_url)
    short_url = f"{request.base_url}{db_url.short_code}"
    return {"original_url": db_url.original_url, "short_url": short_url,"clicks": db_url.clicks}
from fastapi.responses import RedirectResponse

@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    db_url = crud.get_url_by_code(db, short_code)
    if db_url:
        db_url.clicks += 1
        db.commit()
        return RedirectResponse(url=db_url.original_url)
    raise HTTPException(status_code=404, detail="URL not found")
@app.get("/analytics/{short_code}")
def analytics(short_code: str, db: Session = Depends(get_db)):
    db_url = crud.get_url_by_code(db, short_code)
    if db_url:
        return {
            "original_url": db_url.original_url,
            "short_code": db_url.short_code,
            "clicks": db_url.clicks,
            "created_at": db_url.created_at
        }
    raise HTTPException(status_code=404, detail="Short URL not found")

