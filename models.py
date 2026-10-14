"""Shared domain models for catalog and shopping workflows."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    brand: str
    price: float
    processor: str
    ram: str
    storage: str
    battery_life: str
    category: str
    stock: int
    rating: float
    description: str = ""
    review_summary: str = ""

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "Product":
        return cls(
            product_id=str(row["product_id"]),
            product_name=str(row["product_name"]),
            brand=str(row["brand"]),
            price=float(row["price"]),
            processor=str(row.get("processor", "Not specified")),
            ram=str(row.get("ram", "Not specified")),
            storage=str(row.get("storage", "Not specified")),
            battery_life=str(row.get("battery_life", "Not specified")),
            category=str(row.get("category", "Other")),
            stock=int(row.get("stock", 0)),
            rating=float(row.get("rating", 0)),
            description=str(row.get("description", "")),
            review_summary=str(row.get("review_summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShoppingRequirements:
    customer_requirement: str
    budget: float
    preferred_ram: str = ""
    category: str = "Laptop"
    use_case: str = ""
