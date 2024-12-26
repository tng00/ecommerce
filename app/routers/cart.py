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


######################################################################
                            #Cart_route
######################################################################

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

        # Сначала обновляем состояние корзины
        await update_cart_state(db, user_id)

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

async def calculate_total_cost(db: AsyncSession, user_id: int) -> float:
    """
    Рассчитывает общую стоимость корзины для пользователя.
    """
    total_query = text("""
        SELECT SUM(p.price * c.quantity) AS total_cost
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = :user_id
    """)
    result = await db.execute(total_query, {"user_id": user_id})
    return result.scalar() or 0  # Если корзина пуста, вернуть 0


async def update_cart_state(db: AsyncSession, user_id: int):
    """
    Обновляет состояние корзины для пользователя.
    Удаляет позиции с нулевым количеством и синхронизирует актуальные данные товаров.
    """
    # Удаляем записи с нулевым количеством на случай несогласованности данных
    delete_empty_items_query = text("""
        DELETE FROM cart
        WHERE user_id = :user_id AND quantity <= 0
    """)
    await db.execute(delete_empty_items_query, {"user_id": user_id})

        # Удаляем товары с нулевым остатком на складе
    delete_out_of_stock_query = text("""
        DELETE FROM cart
        USING products p
        WHERE cart.product_id = p.id
        AND cart.user_id = :user_id
        AND p.stock = 0
    """)
    await db.execute(delete_out_of_stock_query, {"user_id": user_id})


    # Обновляем данные корзины с учетом текущего состояния товаров (активность, наличие на складе)
    update_cart_query = text("""
        UPDATE cart
        SET quantity = LEAST(quantity, p.stock)  -- Устанавливаем количество не больше доступного на складе
        FROM products p
        WHERE cart.product_id = p.id
        AND cart.user_id = :user_id
        AND p.is_active = TRUE  -- Только активные товары
    """)
    await db.execute(update_cart_query, {"user_id": user_id})

    # Удаляем записи для товаров, которые более недоступны
    delete_inactive_items_query = text("""
        DELETE FROM cart
        USING products p
        WHERE cart.product_id = p.id
        AND cart.user_id = :user_id
        AND p.is_active = FALSE
    """)
    await db.execute(delete_inactive_items_query, {"user_id": user_id})

    await db.commit()


@router.delete("/remove/{product_id}")
async def remove_item_from_cart(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Удалить товар из корзины и обновить её состояние.
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

        # Обновляем корзину
        await update_cart_state(db, user_id)

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


@router.put("/update")
async def update_cart(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    quantities: dict[int, int] = Body(...),  # JSON: {product_id: quantity}
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

        # Обновляем корзину
        await update_cart_state(db, user_id)

        # Рассчитываем общую стоимость корзины
        total_cost = await calculate_total_cost(db, user_id)

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


######################################################################
                            #Cart_db
######################################################################
