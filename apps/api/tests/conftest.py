import os
from pathlib import Path

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{Path(__file__).parent / 'test.db'}"
os.environ["APPROVE_AND_PUBLISH_ENABLED"] = "false"
os.environ["KILL_SWITCH"] = "false"
os.environ["WP_LIVE"] = "false"
os.environ["DEMO_INSTANT_FULFILL"] = "false"
os.environ["DEMO_GROK_WORKER"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app
from app.seed import seed_if_empty


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_if_empty()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
