from fastapi import APIRouter, Depends, Request, HTTPException, status, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas import AddToCartRequest
from app.backend.db_depends import get_db
from app.routers.auth import get_current_user
from pydantic import BaseModel
from yookassa import Configuration, Payment, Refund
import uuid

idempotence_key = str(uuid.uuid4())
Configuration.account_id = "1005331"
Configuration.secret_key = "test_JE0B3RMdXgc_KdjzMj-aIdLdJW-cANg1KC2pgUR_xd0"

# Настройка маршрутов и шаблонов
router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def cart(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Страница корзины пользователя.
    """
    user_id = current_user.get("id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    try:
        # SQL запрос для получения содержимого корзины
        query = text("""
            SELECT 
                c.product_id, 
                p.name, 
                p.description, 
                p.price, 
                p.stock, 
                c.quantity, 
                (p.price * c.quantity) AS total_cost
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = :user_id
        """)
        result = await db.execute(query, {"user_id": user_id})
        cart_items = result.fetchall()

        # Преобразование результатов в список словарей
        cart_list = [
            {
                "product_id": item[0],  # product_id
                "name": item[1],        # name
                "description": item[2], # description
                "price": item[3],       # price
                "stock": item[4],       # stock
                "quantity": item[5],    # quantity
                "total_cost": item[6],  # total_cost
            }
            for item in cart_items
        ]

        # Общая стоимость товаров
        total_cost = sum(item["total_cost"] for item in cart_list)

        return templates.TemplateResponse(
            "cart.html",
            {
                "request": request,
                "cart_items": cart_list,
                "total_cost": total_cost,
                "user": current_user,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Произошла ошибка при загрузке корзины: {str(e)}"
        )

@router.put("/update")
async def update_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
    quantities: Annotated[dict[int, int], Body(...)],  # JSON: {product_id: quantity}
):
    """
    Обновить количество товаров в корзине.
    """
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не авторизован"
        )

    try:
        async with db.begin():  # Начинаем транзакцию
            for product_id, quantity in quantities.items():
                quantity = int(quantity)
                if quantity <= 0:
                    # Удаляем товар из корзины, если количество <= 0
                    delete_query = text("""
                        DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
                    """)
                    await db.execute(delete_query, {"user_id": user_id, "product_id": product_id})
                else:
                    # Проверяем доступность товара
                    stock_query = text("""
                        SELECT stock, is_active FROM products WHERE id = :product_id
                    """)
                    stock_result = await db.execute(stock_query, {"product_id": product_id})
                    stock_data = stock_result.fetchone()

                    if not stock_data or not stock_data.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Товар с ID {product_id} недоступен для обновления."
                        )

                    if quantity > stock_data.stock:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Недостаточно товара на складе для продукта {product_id}."
                        )

                    # Обновляем количество товара в корзине
                    update_query = text("""
                        UPDATE cart 
                        SET quantity = :quantity 
                        WHERE user_id = :user_id AND product_id = :product_id
                    """)
                    await db.execute(update_query, {
                        "quantity": quantity,
                        "user_id": user_id,
                        "product_id": product_id
                    })

        # Рассчитываем общую стоимость корзины
        total_query = text("""
            SELECT SUM(p.price * c.quantity) AS total_cost
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = :user_id
        """)
        result = await db.execute(total_query, {"user_id": user_id})
        total_cost = result.scalar() or 0

        return {"status": "success", "total_cost": total_cost}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении корзины: {str(e)}"
        )

@router.post("/add")
async def add_item_to_cart(
    request_data: AddToCartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Добавить товар в корзину.
    """
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Необходимо войти в систему.")

    product_id = request_data.product_id
    quantity = request_data.quantity

    try:
        # Проверяем, существует ли товар с таким ID
        product_query = text("SELECT id, stock, is_active FROM products WHERE id = :product_id")
        product_result = await db.execute(product_query, {"product_id": product_id})
        product = product_result.fetchone()

        if not product or not product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден или недоступен.")

        # Проверяем, что количество корректно
        if quantity < 1 or quantity > product.stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректное количество товара.")

        # Добавляем товар в корзину
        existing_query = text(
            "SELECT quantity FROM cart WHERE user_id = :user_id AND product_id = :product_id"
        )
        existing_result = await db.execute(existing_query, {"user_id": user_id, "product_id": product_id})
        existing_item = existing_result.fetchone()

        if existing_item:
            # Обновляем количество, если товар уже есть в корзине
            update_query = text(
                """
                UPDATE cart SET quantity = quantity + :quantity
                WHERE user_id = :user_id AND product_id = :product_id
                """
            )
            await db.execute(update_query, {"quantity": quantity, "user_id": user_id, "product_id": product_id})
        else:
            # Добавляем новый товар в корзину
            insert_query = text(
                """
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (:user_id, :product_id, :quantity)
                """
            )
            await db.execute(insert_query, {"user_id": user_id, "product_id": product_id, "quantity": quantity})

        # Фиксируем изменения
        await db.commit()

        return {"success": True, "message": "Товар успешно добавлен в корзину."}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при добавлении товара в корзину: {e}",
        )




@router.delete("/remove/{product_id}")
async def remove_item_from_cart(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Удалить товар из корзины.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Удаляем товар из корзины
        delete_query = text("""
            DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
        """)
        await db.execute(delete_query, {"user_id": user_id, "product_id": product_id})
        await db.commit()

        # Рассчитываем общую стоимость корзины
        total_query = text("""
            SELECT SUM(p.price * c.quantity) AS total_cost
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = :user_id
        """)
        result = await db.execute(total_query, {"user_id": user_id})
        total_cost = result.scalar() or 0  # Если корзина пуста, вернуть 0

        return {"status": "success", "total_cost": total_cost}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении товара: {str(e)}")


######################################################################
                            #Cart_route
######################################################################




######################################################################
                            #Cart_db
######################################################################


# async def add_to_cart(pool: asyncpg.pool.Pool, user_id: int, product_id: int, quantity: int):
#     """
#     Добавить товар в корзину пользователя.
#     """
#     async with pool.acquire() as conn:
#         # Проверяем, есть ли уже этот товар в корзине пользователя
#         existing = await conn.fetchrow("""
#             SELECT quantity FROM cart WHERE user_id = $1 AND product_id = $2
#         """, user_id, product_id)

#         if existing:
#             # Обновляем количество товара в корзине
#             await conn.execute("""
#                 UPDATE cart SET quantity = quantity + $1 WHERE user_id = $2 AND product_id = $3
#             """, quantity, user_id, product_id)
#         else:
#             # Проверяем, активен ли продукт и есть ли на складе
#             product = await conn.fetchrow("""
#                 SELECT stock, is_active FROM products WHERE id = $1
#             """, product_id)

#             if not product or not product["is_active"]:
#                 raise ValueError(f"Товар с ID {product_id} недоступен для покупки.")
#             if product["stock"] < quantity:
#                 raise ValueError(f"Недостаточно товара на складе для продукта {product_id}.")

#             # Добавляем новый товар в корзину
#             await conn.execute("""
#                 INSERT INTO cart (user_id, product_id, quantity)
#                 VALUES ($1, $2, $3)
#             """, user_id, product_id, quantity)


# async def get_cart_items(pool: asyncpg.pool.Pool, user_id: int):
#     """
#     Получить все товары в корзине пользователя.
#     """
#     async with pool.acquire() as conn:
#         return await conn.fetch("""
#             SELECT product_id, name, description, price, stock, quantity, total_cost, image_url
#             FROM cart_details
#             WHERE user_id = $1
#         """, user_id)

# async def update_cart_quantities(pool: asyncpg.pool.Pool, user_id: int, quantities: dict):
#     """
#     Обновить количество товаров в корзине пользователя.
#     """
#     async with pool.acquire() as conn:
#         async with conn.transaction():
#             for product_id, quantity in quantities.items():
#                 quantity = int(quantity)
#                 if quantity <= 0:
#                     # Удаляем товар из корзины, если количество <= 0
#                     await conn.execute("""
#                         DELETE FROM cart WHERE user_id = $1 AND product_id = $2
#                     """, user_id, product_id)
#                 else:
#                     # Проверяем доступность товара на складе
#                     product = await conn.fetchrow("""
#                         SELECT stock, is_active FROM products WHERE id = $1
#                     """, product_id)
#                     if not product or not product["is_active"]:
#                         raise ValueError(f"Товар с ID {product_id} недоступен для обновления.")
#                     if quantity > product["stock"]:
#                         raise ValueError(f"Недостаточно товара на складе для продукта {product_id}.")
                    
#                     await conn.execute("""
#                         UPDATE cart SET quantity = $1 WHERE user_id = $2 AND product_id = $3
#                     """, quantity, user_id, product_id)

# async def remove_from_cart(pool: asyncpg.pool.Pool, user_id: int, product_id: int):
#     """
#     Удалить товар из корзины пользователя.
#     """
#     async with pool.acquire() as conn:
#         await conn.execute("""
#             DELETE FROM cart WHERE user_id = $1 AND product_id = $2
#         """, user_id, product_id)
