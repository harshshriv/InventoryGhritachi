# InventoryGhritachi

A boutique inventory tracking app built with **FastAPI** — a JSON API plus a
lightweight web UI for managing stock. Prices are shown in **AED**.

## Features

- Create, read, update, and delete inventory items
- Per item: number, category, name, size, current stock, on order, max capacity,
  price/unit, cost/unit, sold price, and stock status (In Stock / Sold)
- Auto-computed fields: price-to-cost ratio, in-store + on-order, total cost in
  stock, total retail value in stock, and an **overstocked** flag
- Search (name/category), filter by category and status, and an overstocked-only view
- Dashboard stats: in-stock count, units, stock cost value, retail value, sold
  count, sold revenue, and overstocked count
- First run auto-seeds the catalogue from `data/inventory_seed.csv`
- Interactive docs at `/docs` (Swagger) and `/redoc`

## Tech stack

- FastAPI + Uvicorn
- SQLAlchemy 2.0 ORM (SQLite by default)
- Jinja2 + vanilla JS for the UI
- pytest for tests

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Then open:

- UI dashboard: http://127.0.0.1:8000/
- API docs:     http://127.0.0.1:8000/docs

The database is created automatically as `inventory.db` and, when empty, is
seeded from `data/inventory_seed.csv`. Override the location with the
`DATABASE_URL` environment variable. To re-seed, delete `inventory.db` and
restart.

## API

| Method | Path                 | Description                          |
| ------ | -------------------- | ------------------------------------ |
| GET    | `/api/items`         | List items (`search`, `category`, `status`, `overstocked` query params) |
| POST   | `/api/items`         | Create an item                       |
| GET    | `/api/items/{id}`    | Get one item                         |
| PUT    | `/api/items/{id}`    | Update an item                       |
| DELETE | `/api/items/{id}`    | Delete an item                       |
| GET    | `/api/meta`          | Categories + next free item number   |
| GET    | `/api/stats`         | Aggregate inventory stats            |

## Tests

```bash
pip install -r requirements.txt
pytest
```

## Project layout

```
app/
  main.py        FastAPI app, API routes, UI route
  database.py    SQLAlchemy engine/session
  models.py      Item ORM model (+ computed fields)
  schemas.py     Pydantic request/response models
  crud.py        Database operations
  seed.py        CSV importer (first-run seeding)
  templates/     Jinja2 UI
  static/        CSS + JS
data/
  inventory_seed.csv   Starting catalogue
tests/
  test_api.py    API + UI + seed tests
```
