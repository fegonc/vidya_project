from datetime import datetime

from pydantic import BaseModel


class VendaSchema(BaseModel):
    product_name: str
    category: str
    quantity: int
    unit_price: float


class VendaResponse(VendaSchema):
    id: int
    sale_date: datetime


class VendasList(BaseModel):
    sales: list[VendaResponse]