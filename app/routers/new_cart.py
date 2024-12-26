# async def get_cart_quantities(db: AsyncSession, user_id: int) -> dict[int, int]:
#     query = text("""
#         SELECT product_id, quantity FROM cart WHERE user_id = :user_id
#     """)
#     result = await db.execute(query, {"user_id": user_id})
#     rows = result.fetchall()
#     return {row.product_id: row.quantity for row in rows}


# # Функция проверки авторизации
# async def get_user_id(current_user: dict) -> int:
#     user_id = current_user.get("id")
#     if not user_id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Пользователь не авторизован"
#         )
#     return user_id

# # Функция удаления товара из корзины
# async def remove_from_cart(db: AsyncSession, user_id: int, product_id: int):
#     delete_query = text("""
#         DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
#     """)
#     await db.execute(delete_query, {"user_id": user_id, "product_id": product_id})

# # Функция проверки доступности товара
# async def validate_product_availability(db: AsyncSession, product_id: int, quantity: int, user_id: int):
#     stock_query = text("""
#         SELECT stock, is_active FROM products WHERE id = :product_id
#     """)
#     stock_result = await db.execute(stock_query, {"product_id": product_id})
#     stock_data = stock_result.fetchone()

#     if not stock_data or not stock_data.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Товар с ID {product_id} недоступен для обновления."
#         )

#     if stock_data.stock == 0:
#         # Удаляем товар напрямую
#         delete_query = text("""
#             DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
#         """)
#         await db.execute(delete_query, {"user_id": user_id, "product_id": product_id})
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Товар с ID {product_id} был удален из корзины, так как его нет на складе."
#         )

#     if quantity > stock_data.stock:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Недостаточно товара на складе для продукта {product_id}."
#         )

#     if quantity > stock_data.stock:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Недостаточно товара на складе для продукта {product_id}."
#         )

# # Функция обновления количества товара в корзине
# async def update_cart_quantity(db: AsyncSession, user_id: int, product_id: int, quantity: int):
#     update_query = text("""
#         UPDATE cart 
#         SET quantity = :quantity 
#         WHERE user_id = :user_id AND product_id = :product_id
#     """)
#     await db.execute(update_query, {
#         "quantity": quantity,
#         "user_id": user_id,
#         "product_id": product_id
#     })

# # Функция расчета общей стоимости корзины
# async def calculate_total_cost(db: AsyncSession, user_id: int) -> float:
#     total_query = text("""
#         SELECT SUM(p.price * c.quantity) AS total_cost
#         FROM cart c
#         JOIN products p ON c.product_id = p.id
#         WHERE c.user_id = :user_id
#     """)
#     result = await db.execute(total_query, {"user_id": user_id})
#     return result.scalar() or 0

# # Основной маршрут
# @router.put("/update")
# async def update_cart(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     current_user: Annotated[dict, Depends(get_current_user)],
#     quantities: Annotated[dict[int, int], Body(...)],  # JSON: {product_id: quantity}
# ):
#     """
#     Обновить количество товаров в корзине.
#     """
#     user_id = await get_user_id(current_user)

#     try:
#         async with db.begin():  # Начинаем транзакцию
#             for product_id, quantity in quantities.items():
#                 quantity = int(quantity)
#                 if quantity <= 0:
#                     await remove_from_cart(db, user_id, product_id)
#                 else:
#                     await validate_product_availability(db, product_id, quantity, user_id)
#                     await update_cart_quantity(db, user_id, product_id, quantity)

#         total_cost = await calculate_total_cost(db, user_id)
#         return {"status": "success", "total_cost": total_cost}

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Ошибка при обновлении корзины: {str(e)}"
#         )
