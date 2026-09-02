import os
from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="developer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReviewRecord(Base):
    __tablename__ = "review_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    language: Mapped[str] = mapped_column(String(30))
    score: Mapped[int] = mapped_column(Integer)
    finding_count: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String(500))
    code: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
