# URL Shortener

This project provides a simple URL shortener built with FastAPI and SQLAlchemy. It now supports JWT based authentication and click analytics.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

1. **Start the server**

```bash
uvicorn main:app --reload
```

2. **Get a token**

Send a POST request to `/token` with form fields `username` and `password`. An admin user with username `admin` and password `admin` is created at startup.

3. **Create a short URL**

Send an authenticated POST request to `/shorten` with JSON body:

```json
{"original_url": "https://example.com"}
```

4. **Redirect**

Access `/<short_code>` in the browser to be redirected.

5. **View analytics**

Authenticated users can request `/analytics/{short_code}` to see clicks for their own URLs. Admin users can access `/admin/analytics` to see analytics for all URLs.

## Docker

A simple Dockerfile is included for containerized deployments:

```bash
docker build -t url-shortener .
docker run -p 8000:8000 url-shortener
```

