from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import Base, engine, get_db

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="InventoryGhritachi",
    description="Inventory tracking API + UI",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
@app.get("/api/items", response_model=list[schemas.ItemOut], tags=["items"])
def api_list_items(
    search: str | None = None,
    category: str | None = None,
    low_stock: bool = False,
    db: Session = Depends(get_db),
):
    return crud.list_items(db, search=search, category=category, low_stock=low_stock)


@app.get("/api/items/{item_id}", response_model=schemas.ItemOut, tags=["items"])
def api_get_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post(
    "/api/items",
    response_model=schemas.ItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["items"],
)
def api_create_item(data: schemas.ItemCreate, db: Session = Depends(get_db)):
    if crud.get_item_by_sku(db, data.sku):
        raise HTTPException(status_code=409, detail="SKU already exists")
    return crud.create_item(db, data)


@app.put("/api/items/{item_id}", response_model=schemas.ItemOut, tags=["items"])
def api_update_item(
    item_id: int, data: schemas.ItemUpdate, db: Session = Depends(get_db)
):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if data.sku and data.sku != item.sku and crud.get_item_by_sku(db, data.sku):
        raise HTTPException(status_code=409, detail="SKU already exists")
    return crud.update_item(db, item, data)


@app.delete(
    "/api/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["items"],
)
def api_delete_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    crud.delete_item(db, item)


@app.get("/api/stats", tags=["stats"])
def api_stats(db: Session = Depends(get_db)):
    items = crud.list_items(db)
    return {
        "total_items": len(items),
        "total_units": sum(i.quantity for i in items),
        "total_value": round(sum(i.quantity * i.unit_price for i in items), 2),
        "low_stock_count": sum(1 for i in items if i.low_stock),
    }


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"categories": crud.categories(db)},
    )
