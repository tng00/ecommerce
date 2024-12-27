from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pathlib import Path

class ProductRepository:
    @staticmethod
    async def fetch_products(db, q, category, min_rating, sort_by, sort_order, page, page_size):
        filters = "p.is_active = TRUE"
        if q:
            filters += f" AND p.name ILIKE '%{q}%'"
        if category:
            filters += f" AND p.category_id = {category}"
        if min_rating:
            filters += f" AND p.rating >= {min_rating}"

        offset = (page - 1) * page_size
        query = f"""
            SELECT p.id, p.name, p.description, p.price, p.stock, p.rating, c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE {filters}
            ORDER BY {sort_by} {sort_order.upper()}
            LIMIT {page_size} OFFSET {offset}
        """
        result = await db.execute(text(query))
        products = result.fetchall()
        return {
            "products": [{"id": r.id, "name": r.name, "price": r.price} for r in products],
            "total_products": len(products),
        }

    @staticmethod
    async def get_product_detail(db, product_id, get_user):
        query = text("SELECT * FROM products WHERE id = :id")
        result = await db.execute(query, {"id": product_id})
        product = result.fetchone()
        return {"id": product.id, "name": product.name, "price": product.price}

    @staticmethod
    async def create_product(db, get_user, name, description, price, stock, category):
        query = text("""
            INSERT INTO products (name, description, price, stock, category_id)
            VALUES (:name, :description, :price, :stock, :category_id)
            RETURNING id
        """)
        result = await db.execute(query, {
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "category_id": category,
        })
        await db.commit()
        return result.scalar()

    @staticmethod
    async def save_image(product_id, image_file):
        media_path = Path("app/static/media/")
        media_path.mkdir(parents=True, exist_ok=True)
        file_extension = image_file.filename.split(".")[-1]
        file_name = f"{product_id}.{file_extension}"
        file_path = media_path / file_name
        with file_path.open("wb") as f:
            f.write(await image_file.read())
        return f"/static/media/{file_name}"

    @staticmethod
    async def delete_product(db, product_id):
        query = text("UPDATE products SET is_active = FALSE WHERE id = :product_id")
        await db.execute(query, {"product_id": product_id})
        await db.commit()
