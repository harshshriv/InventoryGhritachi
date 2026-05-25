from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["In Stock", "Sold"]


class ItemBase(BaseModel):
    item_number: int = Field(..., ge=1)
    category: str = Field(default="", max_length=120)
    name: str = Field(..., min_length=1, max_length=200)
    size: str = Field(default="Free", max_length=40)
    description: str = Field(default="")
    current_stock: int = Field(default=0, ge=0)
    on_order: int = Field(default=0, ge=0)
    max_capacity: int = Field(default=1, ge=0)
    price_per_unit: float = Field(default=0.0, ge=0)
    cost_per_unit: float = Field(default=0.0, ge=0)
    sold_price: float | None = Field(default=None, ge=0)
    status: Status = "In Stock"


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    item_number: int | None = Field(default=None, ge=1)
    category: str | None = Field(default=None, max_length=120)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    size: str | None = Field(default=None, max_length=40)
    description: str | None = None
    current_stock: int | None = Field(default=None, ge=0)
    on_order: int | None = Field(default=None, ge=0)
    max_capacity: int | None = Field(default=None, ge=0)
    price_per_unit: float | None = Field(default=None, ge=0)
    cost_per_unit: float | None = Field(default=None, ge=0)
    sold_price: float | None = Field(default=None, ge=0)
    status: Status | None = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    price_to_cost_ratio: float | None
    in_store_plus_on_order: int
    overstocked: bool
    cost_of_current_order: float
    total_cost_in_stock: float
    total_value_in_stock: float
    created_at: datetime
    updated_at: datetime
