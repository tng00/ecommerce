from fastapi import APIRouter, Depends, status, HTTPException, Request, Query
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db import engine
from app.backend.db_depends import get_db
from sqlalchemy import text

from app.routers.search import fetch_products
from app.schemas import CreateProduct
from app.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import File, UploadFile, Form
from pathlib import Path


router = APIRouter(prefix="/product", tags=["product"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def let_admin_get_active_products(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
    q: Annotated[str, Query()] = "",
    category: Annotated[str, Query()] = "",
    min_rating: Annotated[str, Query()] = "",
    sort_by: Annotated[str, Query()] = "stock",
    sort_order: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 5,
):
    try:
        # Проверка прав доступа
        if not (get_user.get("is_admin") or get_user.get("is_supplier")):
            return templates.TemplateResponse("access_denied.html", {"request": request})

        # Преобразование параметров
        category_id = int(category) if category.isdigit() else None
        min_rating_value = (
            float(min_rating) if min_rating and min_rating.replace(".", "", 1).isdigit() else None
        )

        # Получение данных через универсальную функцию
        data = await fetch_products(
            db,
            q=q,
            category_id=category_id,
            min_rating_value=min_rating_value,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        # Запрос для категорий
        categories_query = "SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name"
        categories_result = await db.execute(text(categories_query))
        categories = [{"id": cat[0], "name": cat[1]} for cat in categories_result.fetchall()]


        # Рендеринг страницы
        return templates.TemplateResponse(
            "product.html",
            {
                "request": request,
                "products": data["products"],
                "categories": data["categories"],
                "total_products": data["total_products"],
                "search_query": q,
                "category_id": category_id,
                "min_rating": min_rating_value,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "page": page,
                "page_size": page_size,
                "user": get_user,
            },
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
        query1 = text("""INSERT INTO user_events (user_id, event_type, product_id, quantity)
            VALUES (
                :user_id,
                'view',
                :id,
                0
            );""")
        await db.execute(
                query1,
                {
                    "id": product_id,
                    "user_id":get_user["id"],
                },
            )
        await db.commit()
 

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
