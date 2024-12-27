from fastapi import status
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.presentation.schemas.category_schema import CreateCategory


class CategoryRepository:
    async def get_all_categories(self, db: AsyncSession):
        query = text("SELECT * FROM get_all_categories()")
        result = await db.execute(query)
        return result.fetchall()

    async def is_valid_parent(self, parent_id: int, db: AsyncSession):
        query = text("SELECT id FROM categories WHERE id = :parent_id")
        result = await db.execute(query, {"parent_id": parent_id})
        return result.scalar_one_or_none() is not None

    async def create_category(self, create_category: CreateCategory, slug: str, db: AsyncSession):
        query = text("""
            SELECT create_category_function(:category_name, :category_slug, :category_parent_id)
        """)
        params = {
            "category_name": create_category.name,
            "category_slug": slug,
            "category_parent_id": create_category.parent_id,
        }
        await db.execute(query, params)
        await db.commit()
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}

    async def update_category(self, category_id: int, update_category: CreateCategory, db: AsyncSession):
        query = text("""
            SELECT update_category_function(:category_id, :category_name, :category_parent_id, :category_slug)
        """)
        params = {
            "category_id": category_id,
            "category_name": update_category.name,
            "category_parent_id": update_category.parent_id,
            "category_slug": slugify(update_category.name),
        }
        await db.execute(query, params)
        await db.commit()
        return {"status_code": status.HTTP_200_OK, "transaction": "Category update successful"}

    async def delete_category(self, category_id: int, db: AsyncSession):
        query = text("SELECT delete_category_function(:category_id)")
        await db.execute(query, {"category_id": category_id})
        await db.commit()
        return {"status_code": status.HTTP_200_OK, "transaction": "Category delete is successful"}
