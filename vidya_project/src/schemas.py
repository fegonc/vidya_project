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


class SaleWithCommentResponse(BaseModel):
    """Venda com o comentário que gerou o resultado da busca"""
    id: int
    product_name: str
    category: str
    quantity: int
    unit_price: float
    sale_date: datetime
    comment_id: str
    comment_text: str
    comment_created_at: datetime