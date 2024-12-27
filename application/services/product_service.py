from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify
from pathlib import Path
from app.persistence.repositories.product_repository import ProductRepository


class ProductService:
    @staticmethod
    async def fetch_active_products(request, db, get_user, q, category, min_rating, sort_by, sort_order, page, page_size):
        if not (get_user.get("is_admin") or get_user.get("is_supplier")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

        return await ProductRepository.fetch_products(db, q, category, min_rating, sort_by, sort_order, page, page_size)

    @staticmethod
    async def get_product_detail(request, db, product_id, get_user):
        return await ProductRepository.get_product_detail(db, product_id, get_user)

    @staticmethod
    async def create_product(db, get_user, name, description, price, stock, category, image_file):
        product_id = await ProductRepository.create_product(db, get_user, name, description, price, stock, category)
        if image_file:
            await ProductRepository.save_image(product_id, image_file)
        return {"status_code": status.HTTP_201_CREATED, "message": "Product created successfully"}

    @staticmethod
    async def update_product(db, get_user, product_slug, name, description, price, stock, category, image_file):
        product_data = await ProductRepository.update_product(db, get_user, product_slug, name, description, price, stock, category)
        if image_file:
            await ProductRepository.save_image(product_data["id"], image_file)
        return {"status_code": status.HTTP_200_OK, "message": "Product updated successfully"}

    @staticmethod
    async def delete_product(db, product_id, get_user):
        await ProductRepository.delete_product(db, product_id)
        return {"status_code": status.HTTP_200_OK, "message": "Product deleted successfully"}
