from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import Base, SessionLocal, engine, get_db
from app.seed import seed_if_empty

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(
    title="InventoryGhritachi",
    description="Boutique inventory tracking API + UI",
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
    status: str | None = None,
    overstocked: bool = False,
    db: Session = Depends(get_db),
):
    return crud.list_items(
        db, search=search, category=category, status=status, overstocked=overstocked
    )


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
    if crud.get_item_by_number(db, data.item_number):
        raise HTTPException(status_code=409, detail="Item number already exists")
    return crud.create_item(db, data)


@app.put("/api/items/{item_id}", response_model=schemas.ItemOut, tags=["items"])
def api_update_item(
    item_id: int, data: schemas.ItemUpdate, db: Session = Depends(get_db)
):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if (
        data.item_number
        and data.item_number != item.item_number
        and crud.get_item_by_number(db, data.item_number)
    ):
        raise HTTPException(status_code=409, detail="Item number already exists")
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


@app.get("/api/meta", tags=["meta"])
def api_meta(db: Session = Depends(get_db)):
    return {
        "categories": crud.categories(db),
        "next_item_number": crud.next_item_number(db),
    }


@app.get("/api/stats", tags=["stats"])
def api_stats(db: Session = Depends(get_db)):
    items = crud.list_items(db)
    in_stock = [i for i in items if i.status == "In Stock"]
    sold = [i for i in items if i.status == "Sold"]
    return {
        "total_items": len(items),
        "in_stock_count": len(in_stock),
        "sold_count": len(sold),
        "units_in_stock": sum(i.current_stock for i in in_stock),
        "on_order_units": sum(i.on_order for i in items),
        "overstocked_count": sum(1 for i in items if i.overstocked),
        "stock_cost_value": round(sum(i.total_cost_in_stock for i in in_stock), 2),
        "stock_retail_value": round(sum(i.total_value_in_stock for i in in_stock), 2),
        "sold_revenue": round(sum(i.sold_price or 0 for i in sold), 2),
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
