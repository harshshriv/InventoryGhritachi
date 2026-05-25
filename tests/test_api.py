import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import seed
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
        "item_number": 1,
        "category": "Dhoti Suit",
        "name": "Yellow DS",
        "size": "Free",
        "current_stock": 1,
        "on_order": 0,
        "max_capacity": 1,
        "price_per_unit": 139.0,
        "cost_per_unit": 54.0,
        "status": "In Stock",
    }
    data.update(overrides)
    return data


def test_create_and_computed_fields(client):
    res = client.post("/api/items", json=sample())
    assert res.status_code == 201
    item = res.json()
    assert item["item_number"] == 1
    assert item["price_to_cost_ratio"] == 2.6
    assert item["total_cost_in_stock"] == 54.0
    assert item["total_value_in_stock"] == 139.0
    assert item["in_store_plus_on_order"] == 1
    assert item["overstocked"] is False


def test_duplicate_item_number_rejected(client):
    client.post("/api/items", json=sample())
    res = client.post("/api/items", json=sample(name="White DS"))
    assert res.status_code == 409


def test_overstocked_flag_and_filter(client):
    client.post("/api/items", json=sample(item_number=1, current_stock=2, on_order=1, max_capacity=1))
    client.post("/api/items", json=sample(item_number=2, current_stock=1, max_capacity=1))

    over = client.get("/api/items?overstocked=true").json()
    assert len(over) == 1
    assert over[0]["item_number"] == 1
    assert over[0]["overstocked"] is True


def test_status_filter(client):
    client.post("/api/items", json=sample(item_number=1, status="In Stock"))
    client.post("/api/items", json=sample(item_number=2, status="Sold", sold_price=120.0))

    assert len(client.get("/api/items?status=Sold").json()) == 1
    assert len(client.get("/api/items?status=In Stock").json()) == 1


def test_search_and_category_filter(client):
    client.post("/api/items", json=sample(item_number=1, name="Yellow DS", category="Dhoti Suit"))
    client.post("/api/items", json=sample(item_number=2, name="Black FPCS", category="Floral Print Cord Set"))

    assert len(client.get("/api/items?search=floral").json()) == 1
    assert len(client.get("/api/items?category=Dhoti Suit").json()) == 1


def test_update_item(client):
    item = client.post("/api/items", json=sample()).json()
    res = client.put(
        f"/api/items/{item['id']}",
        json={"status": "Sold", "sold_price": 130.0, "current_stock": 0},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "Sold"
    assert body["sold_price"] == 130.0
    assert body["total_value_in_stock"] == 0.0


def test_delete_item(client):
    item = client.post("/api/items", json=sample()).json()
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get(f"/api/items/{item['id']}").status_code == 404


def test_stats(client):
    client.post("/api/items", json=sample(item_number=1, current_stock=1, price_per_unit=139.0, cost_per_unit=54.0))
    client.post("/api/items", json=sample(item_number=2, status="Sold", sold_price=159.0, current_stock=1))

    stats = client.get("/api/stats").json()
    assert stats["total_items"] == 2
    assert stats["in_stock_count"] == 1
    assert stats["sold_count"] == 1
    assert stats["units_in_stock"] == 1
    assert stats["stock_cost_value"] == 54.0
    assert stats["stock_retail_value"] == 139.0
    assert stats["sold_revenue"] == 159.0


def test_meta_next_number(client):
    client.post("/api/items", json=sample(item_number=5))
    meta = client.get("/api/meta").json()
    assert meta["next_item_number"] == 6
    assert "Dhoti Suit" in meta["categories"]


def test_validation_error(client):
    res = client.post("/api/items", json=sample(current_stock=-1))
    assert res.status_code == 422


def test_dashboard_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "InventoryGhritachi" in res.text


def test_seed_parses_csv():
    items = seed.parse_rows()
    assert len(items) == 89
    first = next(i for i in items if i.item_number == 1)
    assert first.category == "Dhoti Suit"
    assert first.name == "Yellow DS"
    assert first.price_per_unit == 139.0
    assert first.cost_per_unit == 54.0
    sold = [i for i in items if i.status == "Sold"]
    assert len(sold) >= 1
