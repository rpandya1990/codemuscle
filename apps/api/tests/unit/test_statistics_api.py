from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from codemuscle.infrastructure.database.base import Base
from codemuscle.infrastructure.database.session import get_session
from codemuscle.main import app


def test_trend_intervals_counts_and_validation() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            for interval in ("day", "week", "month", "year"):
                response = client.get(
                    "/api/v1/statistics/trends", params={"interval": interval, "count": 5}
                )
                assert response.status_code == 200
                points = response.json()["points"]
                assert len(points) == 5
                assert len({point["period_start"] for point in points}) == 5
                assert all(point["attempts"] == 0 for point in points)
            for params in (
                {"interval": "invalid"},
                {"count": -1},
                {"count": 1001},
                {"count": "1.5"},
            ):
                assert client.get("/api/v1/statistics/trends", params=params).status_code == 422
            assert len(client.get("/api/v1/statistics/trends?count=0").json()["points"]) == 1
            assert len(client.get("/api/v1/statistics/trends?weeks=2").json()["points"]) == 2
            total = client.get("/api/v1/statistics/topics/total")
            assert total.status_code == 200
            assert total.json()["independent_successes"] == 0
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
