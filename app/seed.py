import csv
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models

SEED_CSV = Path(__file__).resolve().parent.parent / "data" / "inventory_seed.csv"


def _money(value: str) -> float:
    value = (value or "").strip().lower().replace("dh", "").replace("aed", "").strip()
    value = value.replace(",", "")
    return float(value) if value else 0.0


def _opt_money(value: str) -> float | None:
    value = (value or "").strip()
    return _money(value) if value else None


def _int(value: str, default: int = 0) -> int:
    value = (value or "").strip()
    return int(float(value)) if value else default


def parse_rows(path: Path = SEED_CSV) -> list[models.Item]:
    items: list[models.Item] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            number = _int(row.get("Part or Item Number", ""))
            if not number:
                continue
            status = (row.get("Stock Status") or "").strip() or models.IN_STOCK
            items.append(
                models.Item(
                    item_number=number,
                    category=(row.get("Item Category") or "").strip(),
                    name=(row.get("Item Name") or "").strip(),
                    size=(row.get("Sizes") or "Free").strip() or "Free",
                    description=(row.get("Description") or "").strip(),
                    current_stock=_int(row.get("Current Stock", ""), 0),
                    on_order=_int(row.get("On Order", ""), 0),
                    max_capacity=_int(row.get("Max Capacity", ""), 1),
                    price_per_unit=_money(row.get("Price Per Unit", "")),
                    cost_per_unit=_money(row.get("Cost Per Unit", "")),
                    sold_price=_opt_money(row.get("Sold Price", "")),
                    status=models.SOLD if status.lower() == "sold" else models.IN_STOCK,
                )
            )
    return items


def seed_if_empty(db: Session) -> int:
    count = db.scalar(select(func.count()).select_from(models.Item))
    if count:
        return 0
    if not SEED_CSV.exists():
        return 0
    items = parse_rows()
    db.add_all(items)
    db.commit()
    return len(items)
