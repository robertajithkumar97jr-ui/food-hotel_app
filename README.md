# Ajith Food Corner

Luxury black-and-gold restaurant ordering app with React, FastAPI and SQLite.

## Run

1. `python -m venv .venv`
2. `.\.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `cd frontend && npm install && npm run build && cd ..`
5. `uvicorn backend.main:app --reload`
6. Open `http://127.0.0.1:8000`

Optional Razorpay test keys: copy `.env.example` to `.env` and set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` before running (or set them in your shell). The API exposes a Razorpay test-order endpoint; without keys checkout uses a clearly-labelled local test payment flow.

Demo admin: `admin@ajithfoodcorner.com` / `admin123`.

## Test

`pytest backend/tests -q`
