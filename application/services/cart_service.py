from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.repositories.cart_repository import CartRepository
from app.application.exceptions import CartServiceException


class CartService:
    def __init__(self, cart_repo: CartRepository):
        self.cart_repo = cart_repo

    async def get_cart(self, user_id: int, reset: bool, db: AsyncSession):
        if reset:
            await self.cart_repo.clear_cart(user_id, db)
        cart_data = await self.cart_repo.fetch_cart(user_id, db)
        total_cost = sum(item["total_cost"] for item in cart_data)
        return {"cart_items": cart_data, "total_cost": total_cost}

    async def add_item_to_cart(self, user_id: int, request_data, db: AsyncSession):
        product_id, quantity = request_data.product_id, request_data.quantity
        if quantity <= 0:
            raise CartServiceException("Количество товара должно быть больше нуля.")
        await self.cart_repo.add_to_cart(user_id, product_id, quantity, db)
        return {"success": True, "message": "Товар успешно добавлен."}

    async def update_cart(self, user_id: int, quantities: dict, db: AsyncSession):
        await self.cart_repo.update_cart(user_id, quantities, db)
        total_cost = await self.cart_repo.calculate_total_cost(user_id, db)
        return {"success": True, "total_cost": total_cost}

    async def remove_item_from_cart(self, user_id: int, product_id: int, db: AsyncSession):
        await self.cart_repo.remove_item(user_id, product_id, db)
        total_cost = await self.cart_repo.calculate_total_cost(user_id, db)
        return {"success": True, "total_cost": total_cost}
