from datetime import datetime

from pydantic import BaseModel, Field


class SaleCommentCreate(BaseModel):
    """Schema para criar comentário - apenas o texto é necessário"""
    text: str = Field(..., min_length=1, max_length=5000, description="Comentário ou observação sobre a venda")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Cliente elogiou a entrega e a qualidade do produto"
            }
        }


class SaleComment(BaseModel):
    """Comentário completo armazenado no MongoDB"""
    sale_id: int
    text: str
    created_at: datetime = Field(default_factory=datetime.now)


class SaleCommentResponse(BaseModel):
    """Resposta com ID do MongoDB incluído"""
    id: str  # ObjectId convertido para string
    sale_id: int
    text: str
    created_at: datetime