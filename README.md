# InventoryGhritachi

A small inventory tracking app built with **FastAPI** — a JSON API plus a
lightweight web UI for managing stock items.

## Features

- Create, read, update, and delete inventory items
- Track quantity, reorder level, unit price, and category per item
- Automatic **low-stock** flag when quantity drops to/below the reorder level
- Search by name/SKU, filter by category, and a low-stock-only view
- Dashboard stats: total items, total units, total inventory value, low-stock count
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

The database is created automatically as `inventory.db`. Override the location
with the `DATABASE_URL` environment variable.

## API

| Method | Path                 | Description                          |
| ------ | -------------------- | ------------------------------------ |
| GET    | `/api/items`         | List items (`search`, `category`, `low_stock` query params) |
| POST   | `/api/items`         | Create an item                       |
| GET    | `/api/items/{id}`    | Get one item                         |
| PUT    | `/api/items/{id}`    | Update an item                       |
| DELETE | `/api/items/{id}`    | Delete an item                       |
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
  models.py      Item ORM model
  schemas.py     Pydantic request/response models
  crud.py        Database operations
  templates/     Jinja2 UI
  static/        CSS + JS
tests/
  test_api.py    API + UI tests
```
