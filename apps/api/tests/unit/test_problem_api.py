from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.models import Attempt, Pattern, Problem, Topic  # noqa: F401
from codemuscle.infrastructure.database.session import get_session
from codemuscle.main import app


def test_problem_api_create_list_and_not_found_error() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        created = client.post(
            "/api/v1/problems",
            json={
                "title": "Binary Search",
                "url": "https://leetcode.com/problems/binary-search/",
                "difficulty": "EASY",
                "topics": ["Binary Search"],
            },
        )
        missing_url = client.post("/api/v1/problems", json={"title": "Missing link"})
        listed = client.get("/api/v1/problems", params={"search": "binary", "page_size": 5000})
        topics = client.get("/api/v1/problems/topics")
        attempt = client.post(
            f"/api/v1/problems/{created.json()['id']}/attempts",
            json={
                "outcome": "SOLVED_INDEPENDENTLY",
                "hint_usage": "NONE",
            },
        )
        history = client.get(f"/api/v1/problems/{created.json()['id']}/attempts")
        missing = client.get("/api/v1/problems/00000000-0000-0000-0000-000000000000")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert missing_url.status_code == 201
    assert listed.json()["total"] == 1
    assert topics.status_code == 200
    assert topics.json() == [{"id": created.json()["topics"][0]["id"], "name": "Binary Search"}]
    assert attempt.status_code == 201
    assert history.json()[0]["id"] == attempt.json()["id"]
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
