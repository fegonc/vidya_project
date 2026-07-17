from contextlib import asynccontextmanager
from datetime import datetime
from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select

from vidya_project.src.database import get_session
from vidya_project.src.models import Vendas
from vidya_project.src.mongo_database import get_mongo_db, mongo_client
from vidya_project.src.mongo_models import (SaleComment, SaleCommentCreate,
                                            SaleCommentResponse)
from vidya_project.src.schemas import (SaleWithCommentResponse, VendaResponse,
                                        VendaSchema, VendasList)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Conectando ao MongoDB...")
    yield
    # Shutdown
    print("Fechando conexão MongoDB...")
    mongo_client.close()

app = FastAPI(title='Vidya Project', lifespan=lifespan)

@app.post('/create_sale/', status_code=HTTPStatus.CREATED, response_model=VendaResponse)
def read_root(venda: VendaSchema, session=Depends(get_session)):
    new_venda = Vendas(
        product_name = venda.product_name,
        category = venda.category,
        quantity = venda.quantity,
        unit_price = venda.unit_price
    )

    session.add(new_venda)
    session.commit()
    session.refresh(new_venda)

    return new_venda

@app.get('/sales/', status_code=HTTPStatus.OK, response_model=VendasList)
def read_sales(session=Depends(get_session), limit: int = 10, offset: int = 0):
    sales = session.scalars(select(Vendas).limit(limit).offset(offset)).all()
    return {'sales': sales}


@app.get('/sales_filter/', status_code=HTTPStatus.OK, response_model=VendasList)
def filter_sales(
    session=Depends(get_session),
    category: str | None = Query(None, description="Filtrar por categoria"),
    start_date: datetime | None = Query(None, description="Data inicial (formato: YYYY-MM-DD)"),
    end_date: datetime | None = Query(None, description="Data final (formato: YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Filtrar vendas por categoria e/ou período.

    Exemplos:
    - /sales_filter/?category=electronics
    - /sales_filter/?start_date=2024-01-01&end_date=2024-12-31
    - /sales_filter/?category=electronics&start_date=2024-01-01
    """
    query = select(Vendas)

    # Aplicar filtros dinamicamente
    if category:
        query = query.where(Vendas.category == category)

    if start_date:
        query = query.where(Vendas.sale_date >= start_date)

    if end_date:
        query = query.where(Vendas.sale_date <= end_date)

    # Aplicar paginação
    query = query.limit(limit).offset(offset)

    sales = session.scalars(query).all()
    return {'sales': sales}

@app.get('/total_revenue', status_code=HTTPStatus.OK)
def revenue(session=Depends(get_session)):
    total = session.query(
        func.sum(Vendas.quantity * Vendas.unit_price)
    ).scalar()
    return {"total_revenue": total or 0}


# ===== INSERIR COMENTÁRIO =====
@app.post('/sales/{sale_id}/comments/', response_model=SaleCommentResponse)
async def create_comment(
    sale_id: int,
    comment_data: SaleCommentCreate,
    session=Depends(get_session),
    mongo_db=Depends(get_mongo_db)
):
    """
    Adicionar comentário/observação sobre uma venda.

    Exemplo:
    POST /sales/1/comments/
    {
        "text": "Cliente elogiou a entrega e a qualidade do produto"
    }
    """
    # 1. Verificar se a venda existe no SQL
    venda = session.scalar(select(Vendas).where(Vendas.id == sale_id))
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    # 2. Criar comentário completo com sale_id da URL
    comment = SaleComment(
        sale_id=sale_id,
        text=comment_data.text,
        created_at=datetime.now()
    )

    # 3. Inserir no MongoDB
    collection = mongo_db["sale_comments"]
    result = await collection.insert_one(comment.model_dump())

    # 4. Retornar com o ID gerado
    return SaleCommentResponse(
        id=str(result.inserted_id),
        **comment.model_dump()
    )



# ===== BUSCA TEXTUAL POR COMENTÁRIO =====
@app.get('/sales/search_by_comment/', response_model=list[SaleWithCommentResponse])
async def search_sales_by_comment(
    q: str = Query(..., min_length=1, description="Texto a buscar nos comentários"),
    session=Depends(get_session),
    mongo_db=Depends(get_mongo_db)
):
    """
    Busca vendas cujos comentários contenham o texto informado.

    Exemplos:
    - /sales/search_by_comment/?q=entrega
    - /sales/search_by_comment/?q=cliente elogiou
    """
    # 1. Busca no MongoDB com regex case-insensitive
    collection = mongo_db["sale_comments"]
    cursor = collection.find({"text": {"$regex": q, "$options": "i"}})
    matched_comments = await cursor.to_list(length=None)

    if not matched_comments:
        return []

    # 2. Busca as vendas correspondentes no SQLite
    sale_ids = [c["sale_id"] for c in matched_comments]
    vendas = session.scalars(select(Vendas).where(Vendas.id.in_(sale_ids))).all()
    vendas_map = {v.id: v for v in vendas}

    # 3. Monta a resposta combinando venda + comentário
    results = []
    for comment in matched_comments:
        venda = vendas_map.get(comment["sale_id"])
        if venda is None:
            continue  # comentário órfão (venda deletada), ignorar
        results.append(
            SaleWithCommentResponse(
                id=venda.id,
                product_name=venda.product_name,
                category=venda.category,
                quantity=venda.quantity,
                unit_price=venda.unit_price,
                sale_date=venda.sale_date,
                comment_id=str(comment["_id"]),
                comment_text=comment["text"],
                comment_created_at=comment["created_at"],
            )
        )

    return results

