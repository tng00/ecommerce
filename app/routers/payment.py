



# async def create_payment(create_order, order_id: int):
#     check_id = str(uuid.uuid4())
#     total_amount = sum(item.quantity * item.price for item in create_order.items)
#     payment = Payment.create({
#         "amount": {
#             "value": str(total_amount),
#             "currency": "RUB"
#         },
#         "confirmation": {
#             "type": "redirect",
#             "return_url": f"https://www.example.com/return_url/{order_id}"
#         },
#         "capture": True,
#         "description": f"Заказ №{order_id}"
#     }, uuid.uuid4())

#     # Сохраняем ссылку на оплату в базе данных
#     query = text("""
#         UPDATE orders SET payment_status = :payment_status, payment_url = :payment_url WHERE id = :order_id
#     """)
#     await db.execute(query, {
#         "payment_status": "pending",
#         "payment_url": payment.confirmation.confirmation_url,
#         "order_id": order_id
#     })
#     await db.commit()

#     return payment


# @router.get("/resume-payment/{order_id}")
# async def resume_payment(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     order_id: int,
#     get_user: Annotated[dict, Depends(get_current_user)],
# ):
#     query = text("""
#         SELECT payment_url, payment_status FROM orders WHERE id = :order_id AND user_id = :user_id
#     """)
#     result = await db.execute(query, {
#         "order_id": order_id,
#         "user_id": get_user.get("id")
#     })
#     order = result.fetchone()

#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found.")

#     if order.payment_status == "completed":
#         raise HTTPException(status_code=400, detail="Payment already completed.")

#     return {"payment_url": order.payment_url}


# @router.post("/payment-webhook")
# async def payment_webhook(payload: dict, db: Annotated[AsyncSession, Depends(get_db)]):
#     payment_id = payload.get("payment_id")
#     status = payload.get("status")

#     if not payment_id or not status:
#         raise HTTPException(status_code=400, detail="Invalid payload.")

#     # Обновление статуса платежа
#     query = text("""
#         UPDATE orders SET payment_status = :payment_status WHERE payment_id = :payment_id
#     """)
#     await db.execute(query, {
#         "payment_status": status,
#         "payment_id": payment_id
#     })
#     await db.commit()

#     return {"status": "success"}



