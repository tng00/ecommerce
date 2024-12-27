from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.presentation.schemas.review_schema import CreateReview


class ReviewRepository:
    async def get_reviews_by_user(self, user_id: int, db: AsyncSession):
        query = text("SELECT * FROM get_active_reviews() WHERE user_id = :user_id")
        result = await db.execute(query, {"user_id": user_id})
        return result.fetchall()

    async def get_all_reviews(self, db: AsyncSession):
        query = text("SELECT * FROM get_active_reviews()")
        result = await db.execute(query)
        return result.fetchall()

    async def review_exists(self, user_id: int, product_id: int, db: AsyncSession):
        query = text(
            """
            SELECT id FROM reviews WHERE user_id = :user_id AND product_id = :product_id
            """
        )
        result = await db.execute(query, {"user_id": user_id, "product_id": product_id})
        return result.scalars().first() is not None

    async def create_review(
        self, user_id: int, create_review: CreateReview, db: AsyncSession
    ):
        query = text(
            """
            SELECT create_review_function(
                :review_product_id, 
                :review_user_id, 
                :review_rating, 
                :review_comment
            )
            """
        )
        params = {
            "review_product_id": create_review.product_id,
            "review_user_id": user_id,
            "review_rating": create_review.rating,
            "review_comment": create_review.comment,
        }
        await db.execute(query, params)
        await db.commit()
        return {"status": "Review created successfully"}
