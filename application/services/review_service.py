from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.repositories.review_repository import ReviewRepository
from app.presentation.schemas.review_schema import CreateReview


class ReviewService:
    def __init__(self, review_repo: ReviewRepository):
        self.review_repo = review_repo

    async def get_active_reviews(self, current_user: dict, db: AsyncSession):
        if current_user.get("is_customer"):
            return await self.review_repo.get_reviews_by_user(
                user_id=current_user["id"], db=db
            )
        return await self.review_repo.get_all_reviews(db=db)

    async def create_review(
        self, current_user: dict, create_review: CreateReview, db: AsyncSession
    ):
        user_id = current_user["id"]
        product_id = create_review.product_id

        # Проверка на наличие отзыва
        if await self.review_repo.review_exists(user_id, product_id, db):
            raise HTTPException(
                status_code=400, detail="You have already left a review for this product."
            )

        # Создание отзыва
        return await self.review_repo.create_review(user_id, create_review, db)
