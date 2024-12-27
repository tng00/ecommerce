from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class CartRepository:
    async def fetch_cart(self, user_id: int, db: AsyncSession):
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
        return result.fetchall()

    async def clear_cart(self, user_id: int, db: AsyncSession):
        query = text("DELETE FROM cart WHERE user_id = :user_id")
        await db.execute(query, {"user_id": user_id})
        await db.commit()

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int, db: AsyncSession):
        existing_query = text("""
            SELECT quantity FROM cart WHERE user_id = :user_id AND product_id = :product_id
        """)
        existing_result = await db.execute(existing_query, {"user_id": user_id, "product_id": product_id})
        existing_item = existing_result.fetchone()

        if existing_item:
            query = text("""
                UPDATE cart SET quantity = quantity + :quantity
                WHERE user_id = :user_id AND product_id = :product_id
            """)
            await db.execute(query, {"quantity": quantity, "user_id": user_id, "product_id": product_id})
        else:
            query = text("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (:user_id, :product_id, :quantity)
            """)
            await db.execute(query, {"user_id": user_id, "product_id": product_id, "quantity": quantity})
        await db.commit()

    async def update_cart(self, user_id: int, quantities: dict, db: AsyncSession):
        for product_id, quantity in quantities.items():
            if quantity <= 0:
                query = text("""
                    DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
                """)
            else:
                query = text("""
                    UPDATE cart SET quantity = :quantity
                    WHERE user_id = :user_id AND product_id = :product_id
                """)
            await db.execute(query, {"quantity": quantity, "user_id": user_id, "product_id": product_id})
        await db.commit()

    async def remove_item(self, user_id: int, product_id: int, db: AsyncSession):
        query = text("""
            DELETE FROM cart WHERE user_id = :user_id AND product_id = :product_id
        """)
        await db.execute(query, {"user_id": user_id, "product_id": product_id})
        await db.commit()

    async def calculate_total_cost(self, user_id: int, db: AsyncSession):
        query = text("""
            SELECT SUM(p.price * c.quantity) AS total_cost
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = :user_id
        """)
        result = await db.execute(query, {"user_id": user_id})
        return result.scalar() or 0
