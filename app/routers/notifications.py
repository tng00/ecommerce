# import aiosmtplib
# from fastapi import APIRouter, Depends, status, HTTPException, Request
# from fastapi.templating import Jinja2Templates
# from typing import Annotated
# from email.message import EmailMessage
# from app.backend.db_depends import get_db
# from app.routers.auth import get_current_user

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, text
# from app.backend.config import SMTP_CONFIG
# from app.schemas import CreateUser  # Модель пользователя

# # Настройка маршрутов и шаблонов
# router = APIRouter(prefix="/notifications", tags=["notifications"])
# templates = Jinja2Templates(directory="app/templates")


# @router.post("/send-notification/{user_id}")
# async def send_notification_route(
#     user_id: int,
#     subject: str,
#     message: str,
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     API для отправки уведомления пользователю.
#     """
#     try:
#         await send_notification(user_id, subject, message, db)
#         return {"status": "success", "message": f"Email sent to user {user_id}"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}


# async def send_notification(user_id: int, subject: str, message: str, db: AsyncSession):
#     """
#     Отправка уведомления пользователю по email.

#     :param user_id: ID пользователя
#     :param subject: Тема письма
#     :param message: Текст письма
#     :param db: Сессия базы данных
#     """
#     # Получение email пользователя из базы данных
#     query = select(CreateUser.email).where(CreateUser.id == user_id)
#     result = await db.execute(query)
#     user_email = result.scalar()

#     if not user_email:
#         raise ValueError(f"Email для пользователя {user_id} не найден")

#     # Создание письма
#     email = EmailMessage()
#     email["From"] = SMTP_CONFIG["from_email"]
#     email["To"] = user_email
#     email["Subject"] = subject
#     email.set_content(message)

#     # Отправка письма
#     try:
#         await aiosmtplib.send(
#             email,
#             hostname=SMTP_CONFIG["host"],
#             port=SMTP_CONFIG["port"],
#             username=SMTP_CONFIG["username"],
#             password=SMTP_CONFIG["password"],
#             start_tls=True,
#         )
#         print(f"Email успешно отправлен пользователю {user_email}")
#     except Exception as e:
#         print(f"Ошибка отправки email пользователю {user_email}: {e}")
#         raise


# @router.post("/notify_low_recent_buys")
# async def notify_low_recent_buys(
#     db: Annotated[AsyncSession, Depends(get_db)]
# ):
#     # SQL для получения пользователей без заказов за последние 7 дней
#     query = text("""
#         SELECT u.id AS user_id, u.email
#         FROM users u
#         LEFT JOIN (
#             SELECT DISTINCT user_id
#             FROM orders
#             WHERE order_date >= NOW() - INTERVAL '7 days'
#         ) recent_orders
#         ON u.id = recent_orders.user_id
#         WHERE recent_orders.user_id IS NULL;
#     """)
    
#     result = await db.execute(query)
#     users = result.fetchall()

#     if not users:
#         return {"status": "success", "message": "No users found without recent orders"}

#     # Отправляем уведомления
#     for user in users:
#         user_id, email = user
#         subject = "Мы скучаем по вам!"
#         message = (
#             f"Здравствуйте! Мы заметили, что вы не совершали заказов в нашем магазине уже неделю. "
#             f"Загляните к нам, у нас много интересного!"
#         )

#         try:
#             await send_notification(user_id=user_id, subject=subject, message=message)
#         except Exception as e:
#             print(f"Ошибка отправки уведомления пользователю {email}: {e}")

#     return {"status": "success", "message": f"Notifications sent to {len(users)} users"}

# @router.post("/send_custom_notification")
# async def send_custom_notification(
#     user_id: int,
#     subject: str,
#     message: str,
#     db: Annotated[AsyncSession, Depends(get_db)],
# ):
#     try:
#         await send_notification(user_id=user_id, subject=subject, message=message)
#         return {"status": "success", "message": "Notification sent successfully"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to send notification: {e}",
#         )


# @router.get("/get_notifications_by_user_id/{user_id}")
# async def get_notifications_by_user_id(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
#     query = text(
#         """
#         SELECT id, notification_type, status, subject, sent_at
#         FROM notifications
#         WHERE user_id = :user_id
#         ORDER BY sent_at DESC
#         """
#     )
#     result = await db.execute(query, {"user_id": user_id})
#     notifications = result.fetchall()
#     return {"notifications": [dict(row) for row in notifications]}