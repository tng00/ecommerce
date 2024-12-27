from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from yookassa import Configuration

from app.config.config import settings

Configuration.account_id = settings.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


class OrderRepository:
    async def get_orders_by_user_role(self, current_user: dict, db: AsyncSession):
        if current_user.get("is_admin"):
            query = text("SELECT * FROM get_all_orders() ORDER BY id DESC")
        elif current_user.get("is_supplier"):
            query = text("""
                SELECT oi.*
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE p.supplier_id = :user_id
                ORDER BY id DESC
            """)
        else:
            query = text("SELECT * FROM get_all_orders() WHERE user_id = :user_id ORDER BY id DESC")
        result = await db.execute(query, {"user_id": current_user["id"]})
        return result.fetchall()

    async def calculate_total_cost(self, db: AsyncSession, user_id: int):
        query = text("""
            SELECT SUM(price * quantity) AS total_cost
            FROM cart WHERE user_id = :user_id
        """)
        result = await db.execute(query, {"user_id": user_id})
        return result.scalar()

    async def create_order(self, create_order, user_id, total_cost, db):
        query = text("""
            INSERT INTO orders (is_card, is_sbp, user_id, order_date, address, total)
            VALUES (:is_card, :is_sbp, :user_id, :order_date, :address, :total)
            RETURNING id
        """)
        result = await db.execute(query, {
            "is_card": create_order.is_card,
            "is_sbp": create_order.is_sbp,
            "user_id": user_id,
            "order_date": datetime.now(),
            "address": create_order.address,
            "total": total_cost
        })
        await db.commit()
        return result.scalar()

    async def process_payment(self, order_id: int, total_cost: float):
        from yookassa import Payment
        payment = Payment.create({
            "amount": {"value": str(total_cost), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://example.com/return_url"},
            "capture": True,
            "description": f"Order #{order_id}",
        })
        return payment.confirmation.confirmation_url

    async def update_order(self, order_id: int, order_update, db):
        query = text("""
            UPDATE orders SET status = :status WHERE id = :id
        """)
        await db.execute(query, {"status": order_update.status, "id": order_id})
        await db.commit()
        return {"detail": "Order updated successfully"}
