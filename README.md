# Mission Log (Local Execution Tracker)

A lightweight FastAPI + SQLite web app to track daily execution:
- Log entries (category, outcome)
- Daily checklist tasks
- Simple day navigation
- CSV export

## Tech Stack
- **FastAPI** — Modern async Python web framework
- **SQLAlchemy + SQLite** — ORM with lightweight database
- **Jinja2** — Server-side templating
- **Docker** — Containerized deployment
- **Pytest** — Automated testing
- **GitHub Actions** — CI/CD pipeline

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open: http://127.0.0.1:8000

Health check: http://127.0.0.1:8000/health

## Run Tests

```bash
pytest -q
```

## Run with Docker

```bash
docker compose up --build
```

Open: http://localhost:8000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page with logs and tasks |
| GET | `/health` | Health check |
| POST | `/log` | Add a log entry |
| POST | `/task` | Add a task |
| POST | `/task/toggle` | Toggle task done/pending |
| GET | `/export` | Export day's data as CSV |

## Why This Exists

I built this as a personal execution system to track daily progress while training as a Full-Stack AI Engineer (FastAPI/Docker/Systems + GenAI projects).

## License

MIT
