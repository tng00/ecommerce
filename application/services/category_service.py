from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.persistence.repositories.category_repository import CategoryRepository
from app.presentation.schemas.category_schema import CreateCategory
from slugify import slugify


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    async def get_all_categories(self, current_user: dict, db: AsyncSession):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
            )
        return await self.category_repo.get_all_categories(db)

    async def create_category(self, current_user: dict, create_category: CreateCategory, db: AsyncSession):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        category_slug = slugify(create_category.name)

        if create_category.parent_id is not None:
            if not await self.category_repo.is_valid_parent(create_category.parent_id, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with ID {create_category.parent_id} does not exist",
                )

        return await self.category_repo.create_category(create_category, category_slug, db)

    async def update_category(
        self, current_user: dict, category_id: int, update_category: CreateCategory, db: AsyncSession
    ):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        return await self.category_repo.update_category(category_id, update_category, db)

    async def delete_category(self, current_user: dict, category_id: int, db: AsyncSession):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        return await self.category_repo.delete_category(category_id, db)
