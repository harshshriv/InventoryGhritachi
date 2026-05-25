from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models, schemas


def list_items(
    db: Session,
    *,
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    overstocked: bool = False,
) -> list[models.Item]:
    stmt = select(models.Item)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(models.Item.name.ilike(pattern), models.Item.category.ilike(pattern))
        )
    if category:
        stmt = stmt.where(models.Item.category == category)
    if status:
        stmt = stmt.where(models.Item.status == status)
    stmt = stmt.order_by(models.Item.item_number)
    items = list(db.scalars(stmt).all())
    if overstocked:
        items = [item for item in items if item.overstocked]
    return items


def get_item(db: Session, item_id: int) -> models.Item | None:
    return db.get(models.Item, item_id)


def get_item_by_number(db: Session, item_number: int) -> models.Item | None:
    return db.scalar(
        select(models.Item).where(models.Item.item_number == item_number)
    )


def next_item_number(db: Session) -> int:
    current = db.scalar(select(models.Item.item_number).order_by(
        models.Item.item_number.desc()
    ))
    return (current or 0) + 1


def create_item(db: Session, data: schemas.ItemCreate) -> models.Item:
    item = models.Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session, item: models.Item, data: schemas.ItemUpdate
) -> models.Item:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: models.Item) -> None:
    db.delete(item)
    db.commit()


def categories(db: Session) -> list[str]:
    rows = db.scalars(
        select(models.Item.category).where(models.Item.category != "").distinct()
    ).all()
    return sorted(rows)
