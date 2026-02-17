from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import date, timedelta
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

    # Calculate total minutes for the day
    total_minutes = sum((l.duration_min or 0) for l in logs)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "log_date": log_date,
            "logs": logs,
            "tasks": tasks,
            "total_minutes": total_minutes
        }
    )


@app.post("/log")
def add_log(
    text: str = Form(...),
    category: str = Form("General"),
    outcome: str = Form(""),
    duration_min: int = Form(0),
    day: str = Form(None)
):
    db = next(get_db())
    log_date = date.fromisoformat(day) if day else date.today()

    entry = LogEntry(
        log_date=log_date,
        category=category,
        text=text,
        outcome=outcome,
        duration_min=duration_min
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
    writer.writerow(["Type", "Timestamp", "Category", "Text", "Outcome/Status", "Duration"])
    for log in logs:
        writer.writerow(["Log", log.ts.isoformat(), log.category, log.text, log.outcome, log.duration_min or 0])
    
    for task in tasks:
        status = "Done" if task.done else "Pending"
        writer.writerow(["Task", task.ts.isoformat(), "-", task.title, status, "-"])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mission_log_{log_date}.csv"}
    )


@app.get("/export/weekly", response_class=PlainTextResponse)
def export_weekly(day: str = None):
    """Export weekly report as Markdown"""
    db = next(get_db())
    end_day = date.fromisoformat(day) if day else date.today()
    start_day = end_day - timedelta(days=6)

    logs = (
        db.query(LogEntry)
        .filter(LogEntry.log_date >= start_day, LogEntry.log_date <= end_day)
        .order_by(LogEntry.log_date.asc(), LogEntry.ts.asc())
        .all()
    )
    tasks = (
        db.query(Task)
        .filter(Task.log_date >= start_day, Task.log_date <= end_day)
        .all()
    )

    total_minutes = sum((l.duration_min or 0) for l in logs)
    done_tasks = sum(1 for t in tasks if t.done)
    total_tasks = len(tasks)

    # Category totals
    by_cat = {}
    for l in logs:
        by_cat[l.category] = by_cat.get(l.category, 0) + (l.duration_min or 0)

    lines = []
    lines.append(f"# Weekly Execution Report ({start_day} → {end_day})")
    lines.append("")
    lines.append(f"- Total time: **{total_minutes} min** (**{total_minutes/60:.2f} hrs**)")
    lines.append(f"- Tasks: **{done_tasks}/{total_tasks}** completed")
    lines.append("")
    lines.append("## Time by Category")
    for cat, mins in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {cat}: {mins} min ({mins/60:.2f} hrs)")
    lines.append("")
    lines.append("## Daily Notes")
    current = None
    for l in logs:
        if l.log_date != current:
            current = l.log_date
            lines.append(f"### {current}")
        outcome = f" — _{l.outcome}_" if l.outcome else ""
        dur = f" ({l.duration_min}m)" if l.duration_min else ""
        lines.append(f"- **{l.category}**{dur}: {l.text}{outcome}")

    md = "\n".join(lines)
    return md
