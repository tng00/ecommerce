
# # async def handle_cart_update(db: AsyncSession, user_id: int, get_user: dict):
# #     try:
# #         async with db.begin():
# #             cart_quantities = await get_cart_quantities(db, user_id)
# #             await update_cart(db, get_user, cart_quantities)
# #     except HTTPException as e:
# #         raise HTTPException(status_code=e.status_code, detail=e.detail)

# # # Логика создания заказа
# # async def create_order_in_db(db: AsyncSession, create_order, user_id: int):
# #     current_timestamp = datetime.now()
# #     query = text(
# #         """
# #             SELECT create_order(:is_card, :is_sbp, :user_id, :order_date, :address, :total)
# #         """
# #     )
# #     result = await db.execute(
# #         query,
# #         {
# #             "is_card": create_order.is_card,
# #             "is_sbp": create_order.is_sbp,
# #             "user_id": user_id,
# #             "order_date": current_timestamp,
# #             "address": create_order.address,
# #             "total": create_order.total,
# #         },
# #     )
# #     return result.scalar()

# # # Логика добавления элементов заказа в базу данных
# # async def insert_order_items(db: AsyncSession, order_id: int, items):
# #     for item in items:
# #         query = text(
# #             """
# #             INSERT INTO order_items(order_id, product_id, quantity, price)
# #             VALUES (:order_id, :product_id, :quantity, :price)
# #         """
# #         )
# #         await db.execute(
# #             query,
# #             {
# #                 "order_id": order_id,
# #                 "product_id": int(item.product_id),
# #                 "quantity": item.quantity,
# #                 "price": item.price,
# #             },
# #         )
# #     await db.commit()

# # # Генерация платежа
# # async def create_payment(create_order, order_id: int):
# #     check_id = str(uuid.uuid4())
# #     check_file_path = os.path.join(CHECKS_DIR, f"{check_id}.pdf")
# #     total_amount = sum(item.quantity * item.price for item in create_order.items)
# #     payment = Payment.create({
# #             "amount": {
# #                 "value": str(total_amount),
# #                 "currency": "RUB"
# #             },
# #             "confirmation": {
# #                 "type": "redirect",
# #                 "return_url": "https://www.example.com/return_url"
# #             },
# #             "capture": True,
# #             "description": "Заказ №" + str(order_id) 
# #         }, uuid.uuid4())
# #     return payment

# # # Создание заказа
# # @router.post("/create")
# # async def create_order(
# #     db: Annotated[AsyncSession, Depends(get_db)],
# #     create_order: CreateOrder,
# #     get_user: Annotated[dict, Depends(get_current_user)],
# # ):
# #     if get_user.get("is_customer") or get_user.get("is_admin"):
# #         user_id = get_user.get("id")
# #         await handle_cart_update(db, user_id, get_user)
# #         order_id = await create_order_in_db(db, create_order, user_id)
# #         await insert_order_items(db, order_id, create_order.items)
# #         payment = await create_payment(create_order, order_id)

# #         return JSONResponse(content={"payment_url": payment.confirmation.confirmation_url})
# #     else:
# #         raise HTTPException(status_code=403, detail="Access denied")

# #####################################################################
# #####################################################################
# #####################################################################
# @router.post("/create")
# async def create_order(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     create_order: CreateOrder,
#     get_user: Annotated[dict, Depends(get_current_user)],
# ):
#     if get_user.get("is_customer") or get_user.get("is_admin"):
#         user_id = get_user.get("id")

#         # Обновляем корзину перед созданием заказа вне транзакции create_order
#         try:
#             cart_quantities = await get_cart_quantities(db, user_id)
#             await update_cart(db, get_user, cart_quantities)
#         except HTTPException as e:
#             return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

#         try:
#             async with db.begin():  # Начинаем транзакцию для создания заказа
#                 current_timestamp = datetime.now()
#                 query = text(
#                     """
#                         SELECT create_order(:is_card, :is_sbp, :user_id, :order_date, :address, :total)
#                     """
#                 )
#                 result = await db.execute(
#                     query,
#                     {
#                         "is_card": create_order.is_card,
#                         "is_sbp": create_order.is_sbp,
#                         "user_id": user_id,
#                         "order_date": current_timestamp,
#                         "address": create_order.address,
#                         "total": create_order.total,
#                     },
#                 )
#                 order_id = result.scalar()

#                 # Сохранение товаров в заказе
#                 for item in create_order.items:
#                     query = text(
#                         """
#                         INSERT INTO order_items(order_id, product_id, quantity, price)
#                         VALUES (:order_id, :product_id, :quantity, :price)
#                         """
#                     )
#                     await db.execute(
#                         query,
#                         {
#                             "order_id": order_id,
#                             "product_id": int(item.product_id),
#                             "quantity": item.quantity,
#                             "price": item.price,
#                         },
#                     )

#                 # Обновляем идентификатор последнего заказа
#                 update_cart_query = text(
#                     """
#                     UPDATE cart
#                     SET last_order_id = :order_id
#                     WHERE user_id = :user_id
#                     """
#                 )
#                 await db.execute(update_cart_query, {"order_id": order_id, "user_id": user_id})

#                 await db.commit()

#             # Генерация платежа
#             total_amount = sum(item.quantity * item.price for item in create_order.items)
#             payment = Payment.create({
#                 "amount": {
#                     "value": str(total_amount),
#                     "currency": "RUB"
#                 },
#                 "confirmation": {
#                     "type": "redirect",
#                     "return_url": f"/order/{order_id}"
#                 },
#                 "capture": True,
#                 "description": f"Заказ №{order_id}"
#             }, uuid.uuid4())

#             return JSONResponse(content={"payment_url": payment.confirmation.confirmation_url, "order_id": order_id})

#         except Exception as e:
#             await db.rollback()
#             raise HTTPException(status_code=500, detail=f"Ошибка при создании заказа: {str(e)}")


# # @router.post("/create")
# # async def create_order(
# #     db: Annotated[AsyncSession, Depends(get_db)],
# #     create_order: CreateOrder,
# #     get_user: Annotated[dict, Depends(get_current_user)],
# # ):

# #     if get_user.get("is_customer") or get_user.get("is_admin"):
# #         user_id = get_user.get("id")

# #         # Обновляем корзину перед созданием заказа
# #         try:
# #             async with db.begin():  # Начинаем транзакцию для обновления корзины
# #                 cart_quantities = await get_cart_quantities(db, user_id)
# #                 await update_cart(db, get_user, cart_quantities)
# #         except HTTPException as e:
# #             return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


# #         current_timestamp = datetime.now()
# #         query = text(
# #             """
# #                 SELECT create_order(:is_card, :is_sbp, :user_id, :order_date, :address, :total)
# #             """
# #         )
# #         result = await db.execute(
# #             query,
# #             {
# #                 "is_card": create_order.is_card,
# #                 "is_sbp": create_order.is_sbp,
# #                 "user_id": user_id,
# #                 "order_date": current_timestamp,
# #                 "address": create_order.address,
# #                 "total": create_order.total,
# #             },
# #         )
# #         order_id = result.scalar()
# #         print(order_id)
# #         await db.commit()
        
# #         for item in create_order.items:
# #             query = text(
# #                 """
# #                 INSERT INTO order_items(order_id, product_id, quantity, price)
# #                 VALUES (:order_id, :product_id, :quantity, :price)
# #             """
# #             )
# #             await db.execute(
# #                 query,
# #                 {
# #                     "order_id": order_id,
# #                     "product_id": int(item.product_id),
# #                     "quantity": item.quantity,
# #                     "price": item.price,
# #                 },
# #             )
# #             await db.commit()

# #         check_id = str(uuid.uuid4())
# #         check_file_path = os.path.join(CHECKS_DIR, f"{check_id}.pdf")
# #         total_amount = sum(item.quantity * item.price for item in create_order.items)
# #         payment = Payment.create({
# #                 "amount": {
# #                     "value": str(total_amount),
# #                     "currency": "RUB"
# #                 },
# #                 "confirmation": {
# #                     "type": "redirect",
# #                     "return_url": "https://www.example.com/return_url"
# #                 },
# #                 "capture": True,
# #                 "description": "Заказ №" + str(order_id) 
# #             }, uuid.uuid4())

# #         #print(f"ID: {payment.id}")
# #         #print(f"Status: {payment.status}")
# #         #print(f"Paid: {payment.paid}")
# #         #print(f"Amount: {payment.amount.value} {payment.amount.currency}")
# #         #print(f"Confirmation Type: {payment.confirmation.type}")
# #         #print(f"Confirmation URL: {payment.confirmation.confirmation_url}")
# #         #print(f"Created At: {payment.created_at}")
# #         #print(f"Description: {payment.description}")
# #         #print(f"Metadata: {payment.metadata}")
# #         #print(f"Recipient Account ID: {payment.recipient.account_id}")
# #         #print(f"Recipient Gateway ID: {payment.recipient.gateway_id}")
# #         #print(f"Refundable: {payment.refundable}")
# #         #print(f"Test: {payment.test}")
 
# #         return JSONResponse(content={"payment_url": payment.confirmation.confirmation_url})
       