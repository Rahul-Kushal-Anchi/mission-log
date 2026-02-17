from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import date
from db import SessionLocal, init_db
from models import LogEntry, Task
import csv
import io


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield


app = FastAPI(title="Mission Log", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    """Health check endpoint for monitoring and CI"""
    return {"status": "ok"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, day: str = None):
    db = next(get_db())
    log_date = date.fromisoformat(day) if day else date.today()

    logs = db.query(LogEntry).filter(
        LogEntry.log_date == log_date
    ).order_by(LogEntry.ts.asc()).all()
    
    tasks = db.query(Task).filter(
        Task.log_date == log_date
    ).order_by(Task.ts.asc()).all()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "log_date": log_date,
            "logs": logs,
            "tasks": tasks
        }
    )


@app.post("/log")
def add_log(
    text: str = Form(...),
    category: str = Form("General"),
    outcome: str = Form(""),
    day: str = Form(None)
):
    db = next(get_db())
    log_date = date.fromisoformat(day) if day else date.today()

    entry = LogEntry(
        log_date=log_date,
        category=category,
        text=text,
        outcome=outcome
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url=f"/?day={log_date.isoformat()}", status_code=303)


@app.post("/task")
def add_task(title: str = Form(...), day: str = Form(None)):
    db = next(get_db())
    log_date = date.fromisoformat(day) if day else date.today()

    task = Task(log_date=log_date, title=title)
    db.add(task)
    db.commit()
    return RedirectResponse(url=f"/?day={log_date.isoformat()}", status_code=303)


@app.post("/task/toggle")
def toggle_task(task_id: int = Form(...), day: str = Form(None)):
    db = next(get_db())
    t = db.query(Task).filter(Task.id == task_id).first()
    if t:
        t.done = not t.done
        db.commit()

    log_date = date.fromisoformat(day) if day else date.today()
    return RedirectResponse(url=f"/?day={log_date.isoformat()}", status_code=303)


@app.get("/export")
def export_csv(day: str = None):
    """Export logs and tasks for a given day as CSV"""
    db = next(get_db())
    log_date = date.fromisoformat(day) if day else date.today()

    logs = db.query(LogEntry).filter(LogEntry.log_date == log_date).all()
    tasks = db.query(Task).filter(Task.log_date == log_date).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write logs
    writer.writerow(["Type", "Timestamp", "Category", "Text", "Outcome/Status"])
    for log in logs:
        writer.writerow(["Log", log.ts.isoformat(), log.category, log.text, log.outcome])
    
    for task in tasks:
        status = "Done" if task.done else "Pending"
        writer.writerow(["Task", task.ts.isoformat(), "-", task.title, status])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mission_log_{log_date}.csv"}
    )
