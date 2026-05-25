from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

IN_STOCK = "In Stock"
SOLD = "Sold"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(120), default="", index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    size: Mapped[str] = mapped_column(String(40), default="Free")
    description: Mapped[str] = mapped_column(Text, default="")
    current_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_per_unit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sold_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=IN_STOCK, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    @property
    def price_to_cost_ratio(self) -> float | None:
        if not self.cost_per_unit:
            return None
        return round(self.price_per_unit / self.cost_per_unit, 1)

    @property
    def in_store_plus_on_order(self) -> int:
        return self.current_stock + self.on_order

    @property
    def overstocked(self) -> bool:
        return self.in_store_plus_on_order > self.max_capacity

    @property
    def cost_of_current_order(self) -> float:
        return round(self.on_order * self.cost_per_unit, 2)

    @property
    def total_cost_in_stock(self) -> float:
        return round(self.current_stock * self.cost_per_unit, 2)

    @property
    def total_value_in_stock(self) -> float:
        return round(self.current_stock * self.price_per_unit, 2)
