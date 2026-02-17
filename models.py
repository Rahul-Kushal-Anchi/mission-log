from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime, date

Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True)
    log_date = Column(Date, default=date.today, index=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    category = Column(String(50), default="General", index=True)
    text = Column(Text, nullable=False)
    outcome = Column(String(100), default="")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    log_date = Column(Date, default=date.today, index=True)
    ts = Column(DateTime, default=datetime.utcnow)
    title = Column(String(200), nullable=False)
    done = Column(Boolean, default=False)
