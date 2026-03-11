from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()

@table_registry.mapped_as_dataclass
class Vendas:
    __tablename__ = 'vendas'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    product_name: Mapped[str]
    category: Mapped[str] = mapped_column(unique=True)
    quantity: Mapped[int]
    unit_price: Mapped[float]
    sale_date: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )