from typing import Any, Generator


from starlette.testclient import TestClient


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from vidya_project.src.app import app
from vidya_project.src.database import get_session
from vidya_project.src.models import table_registry

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def client() -> Generator[TestClient, Any, None]:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    table_registry.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    table_registry.metadata.drop_all(engine)
    engine.dispose()


def test_create_sale_returns_201(client):
    payload: dict[str, Any] = {
        "product_name": "Notebook Dell",
        "category": "electronics",
        "quantity": 2,
        "unit_price": 3500.00,
    }

    response = client.post("/create_sale/", json=payload)

    assert response.status_code == 201


def test_create_sale_returns_correct_data(client):
    payload: dict[str, Any] = {
        "product_name": "Notebook Dell",
        "category": "electronics",
        "quantity": 2,
        "unit_price": 3500.00,
    }

    response = client.post("/create_sale/", json=payload)
    data = response.json()

    assert data["product_name"] == "Notebook Dell"
    assert data["category"] == "electronics"
    assert data["quantity"] == 2
    assert data["unit_price"] == 3500.00
    assert "id" in data
    assert "sale_date" in data
