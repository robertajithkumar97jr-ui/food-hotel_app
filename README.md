# Ajith Food Corner

Luxury black-and-gold restaurant ordering app with React, FastAPI and SQLite.

## Run

1. `python -m venv .venv`
2. `.\.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `cd frontend && npm install && npm run build && cd ..`
5. `uvicorn backend.main:app --reload`
6. Open `http://127.0.0.1:8000`

Orders do not collect online payments. Set `JWT_SECRET`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in the process environment before starting. The application does not automatically load `.env`.

An admin is created from the environment variables on first startup when no admin exists. Existing databases retain existing accounts.

For Docker, Jenkins, Ansible and EC2 instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Test

`pytest backend/tests -q`
