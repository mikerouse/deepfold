from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    database = make_url(settings.database_url).database
    if database and database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_schema()


def ensure_schema() -> None:
    """Add columns introduced after v0 for SQLite/dev databases that skip Alembic."""
    inspector = inspect(engine)
    dialect = engine.dialect.name
    statements: list[str] = []

    if "drafts" in inspector.get_table_names():
        draft_cols = {col["name"] for col in inspector.get_columns("drafts")}
        if "parked" not in draft_cols:
            if dialect == "sqlite":
                statements.append("ALTER TABLE drafts ADD COLUMN parked BOOLEAN NOT NULL DEFAULT 0")
            else:
                statements.append("ALTER TABLE drafts ADD COLUMN parked BOOLEAN NOT NULL DEFAULT FALSE")
        if "geography" not in draft_cols:
            statements.append("ALTER TABLE drafts ADD COLUMN geography JSON")

    if "outlets" in inspector.get_table_names():
        outlet_cols = {col["name"] for col in inspector.get_columns("outlets")}
        if "county" not in outlet_cols:
            statements.append("ALTER TABLE outlets ADD COLUMN county VARCHAR(128) DEFAULT ''")

    if not statements:
        return
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
