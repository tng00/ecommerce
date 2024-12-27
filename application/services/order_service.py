from sqlalchemy.ext.asyncio import AsyncSession
from app.application.exceptions import OrderServiceException
from app.persistence.repositories.order_repository import OrderRepository
from app.presentation.schemas.order_schema import CreateOrder, OrderUpdate
from datetime import datetime
from yookassa import Configuration
from app.config.config import settings

Configuration.account_id = settings.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


class OrderService:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    async def get_all_orders(self, current_user: dict, db: AsyncSession):
        try:
            return await self.order_repo.get_orders_by_user_role(current_user, db)
        except Exception as e:
            raise OrderServiceException(f"Error retrieving orders: {str(e)}")

    async def create_order(self, create_order: CreateOrder, current_user: dict, db: AsyncSession):
        try:
            user_id = current_user["id"]
            total_cost = await self.order_repo.calculate_total_cost(db, user_id)
            order_id = await self.order_repo.create_order(create_order, user_id, total_cost, db)
            payment_url = await self.order_repo.process_payment(order_id, total_cost)
            return payment_url
        except Exception as e:
            raise OrderServiceException(f"Error creating order: {str(e)}")

    async def update_order(self, order_id: int, order_update: OrderUpdate, current_user: dict, db: AsyncSession):
        try:
            if not current_user.get("is_admin"):
                raise OrderServiceException("Unauthorized to update orders")
            return await self.order_repo.update_order(order_id, order_update, db)
        except Exception as e:
            raise OrderServiceException(f"Error updating order: {str(e)}")
