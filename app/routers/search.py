from fastapi import FastAPI, APIRouter, Depends, status, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, text
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Annotated
from app.backend.db_depends import get_db
from app.routers.auth import get_current_user
from app.routers.category import handle_db_error

router = APIRouter(prefix="/search", tags=["search"])
templates = Jinja2Templates(directory="app/templates")


async def fetch_products(
    db: AsyncSession,
    q: str = "",
    category_id: int = None,
    min_rating_value: float = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 5,
) -> dict:
    """
    Универсальная функция для получения списка продуктов с фильтрацией, сортировкой и пагинацией.
    """
    filters, params = build_filter_conditions(q, category_id, min_rating_value)

    # Вычисление сдвига для пагинации
    offset = (page - 1) * page_size
    params.update({"limit": page_size, "offset": offset})

    # Основной запрос
    sql_query = f"""
        SELECT p.id, p.name, p.description, p.price, p.stock, c.name AS category_name, p.rating, p.image_url
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE {filters}
        ORDER BY p.{sort_by if sort_by in ["name", "price", "stock"] else "name"} 
        {sort_order.upper() if sort_order in ["asc", "desc"] else "ASC"}
        LIMIT :limit OFFSET :offset
    """
    result = await db.execute(text(sql_query), params)
    products = result.fetchall()

    # Подсчет общего количества продуктов
    count_query = f"SELECT COUNT(*) FROM products p WHERE {filters}"
    total_result = await db.execute(text(count_query), params)
    total_products = total_result.scalar()

    # Формирование списка продуктов
    products_list = [
        {
            "id": product[0],
            "name": product[1],
            "description": product[2],
            "price": product[3],
            "stock": product[4],
            "category_name": product[5],
            "rating": product[6],
            "image_url": product[7],
        }
        for product in products
    ]

    # Получение списка категорий
    categories_query = "SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name"
    categories_result = await db.execute(text(categories_query))
    categories = [{"id": cat[0], "name": cat[1]} for cat in categories_result.fetchall()]

    return {
        "products": products_list,
        "categories": categories,
        "total_products": total_products,
    }


def build_filter_conditions(q, category_id, min_rating_value):
    """
    Формирует условия фильтрации для SQL-запросов и параметры.
    """
    filters = ["p.is_active = TRUE"]  # Основное условие
    params = {}

    if q:
        filters.append("(p.name ILIKE :q OR p.description ILIKE :q)")
        params["q"] = f"%{q}%"

    if category_id is not None:
        filters.append("p.category_id = :category")
        params["category"] = category_id

    if min_rating_value is not None:
        filters.append("p.rating >= :min_rating")
        params["min_rating"] = min_rating_value

    return " AND ".join(filters), params


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    q: Annotated[str, Query()] = "",
    category: Annotated[str, Query()] = "",
    min_rating: Annotated[str, Query()] = "",
    sort_by: Annotated[str, Query()] = "name",
    sort_order: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 5
):
    try:
                # Проверка прав доступа
        #if not (get_user.get("is_admin") or get_user.get("is_supplier")):
        #    return templates.TemplateResponse("access_denied.html", {"request": request})

        # Преобразование параметров
        category_id = int(category) if category.isdigit() else None
        min_rating_value = (
            float(min_rating) if min_rating and min_rating.replace(".", "", 1).isdigit() else None
        )

        
                # Получение данных через универсальную функцию
        data = await fetch_products(
            db,
            q=q,
            category_id=category_id,
            min_rating_value=min_rating_value,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        
        # Запрос для категорий
        categories_query = "SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name"
        categories_result = await db.execute(text(categories_query))
        categories = [{"id": cat[0], "name": cat[1]} for cat in categories_result.fetchall()]

        # Возврат шаблона
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": data["products"],
                "categories": data["categories"],
                "total_products": data["total_products"],
                "search_query": q,
                "category_id": category_id,
                "min_rating": min_rating_value,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "page": page,
                "page_size": page_size,
                "user": get_user,
            },
        )

    except Exception as e:
        await handle_db_error(e)

