import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def sample(**overrides):
    data = {
        "name": "Ghee Tin 1kg",
        "sku": "GHE-1KG",
        "category": "Dairy",
        "quantity": 10,
        "reorder_level": 3,
        "unit_price": 12.5,
    }
    data.update(overrides)
    return data


def test_create_and_get_item(client):
    res = client.post("/api/items", json=sample())
    assert res.status_code == 201
    item = res.json()
    assert item["id"] > 0
    assert item["low_stock"] is False

    res = client.get(f"/api/items/{item['id']}")
    assert res.status_code == 200
    assert res.json()["sku"] == "GHE-1KG"


def test_duplicate_sku_rejected(client):
    client.post("/api/items", json=sample())
    res = client.post("/api/items", json=sample(name="Other"))
    assert res.status_code == 409


def test_low_stock_flag_and_filter(client):
    client.post("/api/items", json=sample(sku="A", quantity=2, reorder_level=5))
    client.post("/api/items", json=sample(sku="B", quantity=20, reorder_level=5))

    low = client.get("/api/items?low_stock=true").json()
    assert len(low) == 1
    assert low[0]["sku"] == "A"
    assert low[0]["low_stock"] is True


def test_search_and_category_filter(client):
    client.post("/api/items", json=sample(sku="A", name="Butter", category="Dairy"))
    client.post("/api/items", json=sample(sku="B", name="Rice", category="Grains"))

    assert len(client.get("/api/items?search=but").json()) == 1
    assert len(client.get("/api/items?category=Grains").json()) == 1


def test_update_item(client):
    item = client.post("/api/items", json=sample()).json()
    res = client.put(f"/api/items/{item['id']}", json={"quantity": 0})
    assert res.status_code == 200
    body = res.json()
    assert body["quantity"] == 0
    assert body["low_stock"] is True


def test_delete_item(client):
    item = client.post("/api/items", json=sample()).json()
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get(f"/api/items/{item['id']}").status_code == 404


def test_stats(client):
    client.post("/api/items", json=sample(sku="A", quantity=10, unit_price=2.0))
    client.post("/api/items", json=sample(sku="B", quantity=1, reorder_level=5, unit_price=3.0))

    stats = client.get("/api/stats").json()
    assert stats["total_items"] == 2
    assert stats["total_units"] == 11
    assert stats["total_value"] == 23.0
    assert stats["low_stock_count"] == 1


def test_validation_error(client):
    res = client.post("/api/items", json=sample(quantity=-1))
    assert res.status_code == 422


def test_dashboard_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "InventoryGhritachi" in res.text
