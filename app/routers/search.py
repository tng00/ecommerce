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
        # Преобразование параметров
        category_id = int(category) if category.isdigit() else None
        min_rating_value = (
            float(min_rating) if min_rating and min_rating.replace(".", "", 1).isdigit() else None
        )

        # Генерация фильтров
        filters, params = build_filter_conditions(q, category_id, min_rating_value)

        # Вычисление сдвига для пагинации
        offset = (page - 1) * page_size
        params.update({"limit": page_size, "offset": offset})

        # Основной запрос с фильтрацией, сортировкой и пагинацией
        sql_query = f"""
            SELECT p.id, p.name, p.description, p.price, p.stock, c.name AS category_name, p.rating, p.image_url
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {filters}
            ORDER BY p.{sort_by if sort_by in ["name", "price"] else "name"} 
            {sort_order.upper() if sort_order in ["asc", "desc"] else "ASC"}
            LIMIT :limit OFFSET :offset
        """
        result = await db.execute(text(sql_query), params)
        products = result.fetchall()

        # Подсчет общего количества товаров
        count_query = f"SELECT COUNT(*) FROM products p WHERE {filters}"
        total_result = await db.execute(text(count_query), params)
        total_products = total_result.scalar()

        # Формирование списка продуктов
        product_list = [
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

        # Запрос для категорий
        categories_query = "SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name"
        categories_result = await db.execute(text(categories_query))
        categories = [{"id": cat[0], "name": cat[1]} for cat in categories_result.fetchall()]

        # Возврат шаблона
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": product_list,
                "user": get_user,
                "categories": categories,
                "search_query": q,
                "category_id": category_id,
                "min_rating": min_rating_value,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "page": page,
                "page_size": page_size,
                "total_products": total_products,
            },
        )

    except Exception as e:
        await handle_db_error(e)



# @router.get("/", response_class=HTMLResponse)
# async def home(
#     request: Request,
#     db: Annotated[AsyncSession, Depends(get_db)],
#     get_user: Annotated[dict, Depends(get_current_user)],
#     q: Annotated[str, Query()] = "",
#     category: Annotated[str, Query()] = "",
#     min_rating: Annotated[str, Query()] = "",
#     sort_by: Annotated[str, Query()] = "name",
#     sort_order: Annotated[str, Query()] = "asc"
# ):
#     """
#     Главная страница интернет-магазина с возможностью поиска и фильтрации.
#     """
#     try:
#         # Преобразование параметров
#         category_id = int(category) if category.isdigit() else None
#         min_rating_value = float(min_rating) if min_rating.replace(".", "", 1).isdigit() else None

#         # Базовый запрос
#         sql_query = """
#             SELECT p.id, p.name, p.description, p.price, p.stock, c.name AS category_name, p.rating, p.image_url
#             FROM products p
#             LEFT JOIN categories c ON p.category_id = c.id
#             WHERE p.is_active = TRUE
#         """
#         params = {}

#         # Условия фильтрации
#         if q:
#             sql_query += " AND (p.name ILIKE :q OR p.description ILIKE :q)"
#             params["q"] = f"%{q}%"

#         if category_id is not None:
#             sql_query += " AND p.category_id = :category"
#             params["category"] = category_id

#         if min_rating_value is not None:
#             sql_query += " AND p.rating >= :min_rating"
#             params["min_rating"] = min_rating_value

#         # Сортировка
#         if sort_by not in ["name", "price"]:
#             sort_by = "name"
#         if sort_order not in ["asc", "desc"]:
#             sort_order = "asc"
#         sql_query += f" ORDER BY p.{sort_by} {sort_order.upper()}"

#         # Выполнение запроса
#         result = await db.execute(text(sql_query), params)
#         products = result.fetchall()

#         # Формирование списка продуктов
#         product_list = [
#             {
#                 "id": product[0],
#                 "name": product[1],
#                 "description": product[2],
#                 "price": product[3],
#                 "stock": product[4],
#                 "category_name": product[5],
#                 "rating": product[6],
#                 "image_url": product[7],
#             }
#             for product in products
#         ]

#         # Запрос для категорий
#         categories_query = "SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name"
#         categories_result = await db.execute(text(categories_query))
#         categories = [{"id": cat[0], "name": cat[1]} for cat in categories_result.fetchall()]


#         return templates.TemplateResponse(
#             "index.html",
#             {
#                 "request": request,
#                 "products": product_list,
#                 "user": get_user,
#                 "categories": categories,  # Передаем категории в шаблон
#                 "search_query": q,
#                 "category_id": category_id,
#                 "min_rating": min_rating_value,
#                 "sort_by": sort_by,
#                 "sort_order": sort_order
#             }
#         )


#     except Exception as e:
#         await handle_db_error(e)


