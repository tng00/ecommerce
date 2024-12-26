from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db import engine
from app.backend.db_depends import get_db
from sqlalchemy import text

from app.schemas import CreateProduct
from app.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import File, UploadFile, Form
from pathlib import Path


router = APIRouter(prefix="/product", tags=["product"])

templates = Jinja2Templates(directory="app/templates")

# unused catalog
@router.get("/", response_class=HTMLResponse)
async def get_active_products(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    try:
        query = text("SELECT * FROM get_active_products() ORDER BY id")
        result = await db.execute(query)
        products = result.fetchall()
        products_list = [
            {
                "id": product.id,
                "category_id": product.category_id,
                "category_name": product.category_name,
                "rating": product.rating,
                "is_active": product.is_active,
                "supplier_id": product.supplier_id,
                "price": product.price,
                "stock": product.stock,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "image_url": product.image_url,
            }
            for product in products
        ]
        query = text("SELECT * FROM get_all_categories()")
        result = await db.execute(query)
        categories = result.fetchall()
        categories_list = [
            {
                "id": category[0],  # id
                "is_active": category[1],  # is_active
                "parent_id": category[2],  # parent_id
                "name": category[3],  # name
                "slug": category[4],  # slug
            }
            for category in categories
        ]

        if get_user.get("is_admin") or get_user.get("is_supplier"):
            return templates.TemplateResponse(
                "product.html",
                {"request": request, "products": products_list, "user": get_user, "categories": categories_list},
            )
        else:
            return templates.TemplateResponse(
                "access_denied.html", {"request": request}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{product_id}/", response_class=HTMLResponse)
async def get_product_detail(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    product_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    try:
        query = text("SELECT * FROM products WHERE id = :id")
        result = await db.execute(query, {"id": product_id})
        product = result.fetchone()
        product_detail = [
            {
                "id": product.id,
                "category_id": product.category_id,
                "rating": product.rating,
                "is_active": product.is_active,
                "supplier_id": product.supplier_id,
                "price": product.price,
                "stock": product.stock,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "image_url": product.image_url,
            }
        ]

        # Получаем отзывы о продукте
        reviews_query = text("""
            SELECT 
                r.id,
                r.product_id,
                r.user_id,
                r.rating,
                r.comment,
                p.name AS product_name,
                u.first_name || ' ' || u.last_name AS user_name
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            JOIN users u ON r.user_id = u.id
            WHERE p.is_active = TRUE AND r.product_id = :product_id
        """)
        reviews_result = await db.execute(reviews_query, {"product_id": product_id})
        reviews = reviews_result.fetchall()

        reviews_list = [
            {
                "id": review.id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "user_name": review.user_name,  # Имя пользователя
                "rating": review.rating,
                "comment": review.comment,
            }
            for review in reviews
        ]

        return templates.TemplateResponse(
            "product_page.html",
            {"request": request, "products": product_detail, "reviews": reviews_list, "user": get_user},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )





@router.post("/create")
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    category: int = Form(...),
    image_file: UploadFile = File(None),
):
    if get_user.get("is_supplier") or get_user.get("is_admin"):
        query = text(
            """
            SELECT create_product_function(
                :product_name, 
                :product_description, 
                :product_price, 
                NULL,  -- Временно без URL изображения
                :product_stock, 
                :product_category_id, 
                :product_slug, 
                :product_supplier_id,
                :product_rating
            ) AS product_id
            """
        )
        result = await db.execute(
            query,
            {
                "product_name": name,
                "product_description": description,
                "product_price": price,
                "product_stock": stock,
                "product_category_id": category,
                "product_slug": slugify(name),
                "product_supplier_id": get_user.get("id"),
                "product_rating": 0.0,
            },
        )
        new_product_id = result.scalar() 

        if not new_product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create product.",
            )

        if image_file:
            media_path = Path("app/static/media/")
            media_path.mkdir(parents=True, exist_ok=True)

            file_extension = image_file.filename.split(".")[-1]
            file_name = f"{new_product_id}.{file_extension}"
            file_path = media_path / file_name

            with file_path.open("wb") as f:
                f.write(await image_file.read())

            image_url = f"/static/media/{file_name}"
            update_query = text(
                """
                UPDATE products
                SET image_url = :image_url
                WHERE id = :product_id
                """
            )
            await db.execute(
                update_query,
                {
                    "image_url": image_url,
                    "product_id": new_product_id,
                },
            )
            await db.commit()

        return {
            "status_code": status.HTTP_201_CREATED,
            "transaction": "Successful",
            "product_id": new_product_id,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )




@router.put("/detail/{product_slug}")
async def update_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    product_slug: str,
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    category: int = Form(...),
    image_file: UploadFile = File(None),
):
    query = text(
        """
        SELECT * FROM products WHERE slug = :slug AND is_active = TRUE
        """
    )
    result = await db.execute(query, {"slug": product_slug})
    product_update = result.fetchone()

    if product_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found",
        )

    if get_user.get("is_supplier") or get_user.get("is_admin"):
        if get_user.get("id") == product_update.supplier_id or get_user.get("is_admin"):
            image_url = (
                product_update.image_url
            )
            if image_file:
                media_path = Path("app/static/media/")
                media_path.mkdir(parents=True, exist_ok=True)

                file_extension = image_file.filename.split(".")[-1]
                file_name = f"{product_update.id}.{file_extension}"
                file_path = media_path / file_name

                with file_path.open("wb") as f:
                    f.write(await image_file.read())

                image_url = f"/static/media/{file_name}"

            query = text(
                """
                SELECT update_product_function(
                    :product_slug_input,
                    :product_name,
                    :product_description,
                    :product_price,
                    :product_image_url,
                    :product_stock,
                    :product_category_id,
                    :product_slug
                )
                """
            )
            await db.execute(
                query,
                {
                    "product_slug_input": product_slug,
                    "product_name": name,
                    "product_description": description,
                    "product_price": price,
                    "product_image_url": image_url,
                    "product_stock": stock,
                    "product_category_id": category,
                    "product_slug": slugify(name),
                },
            )
            await db.commit()

            return {
                "status_code": status.HTTP_200_OK,
                "transaction": "Product update is successful",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this product",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )


@router.delete("/delete")
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):

    query = text(
        """
        SELECT * FROM products WHERE id = :product_id
    """
    )
    result = await db.execute(query, {"product_id": product_id})
    product_delete = result.fetchone()

    if product_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There is no product found"
        )

    if get_user.get("is_supplier") or get_user.get("is_admin"):
        if get_user.get("id") == product_delete.supplier_id or get_user.get("is_admin"):
            delete_query = text(
                """
                UPDATE products
                SET is_active = FALSE
                WHERE id = :product_id
            """
            )
            await db.execute(delete_query, {"product_id": product_id})
            await db.commit()
            return {
                "status_code": status.HTTP_200_OK,
                "transaction": "Product delete is successful",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to use this method",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )
