from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from typing import Annotated

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy import insert
from app.schemas import CreateCategory
from sqlalchemy.exc import SQLAlchemyError

from slugify import slugify

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.routers.auth import get_current_user
from sqlalchemy import text


router = APIRouter(prefix="/category", tags=["category"])


def handle_db_error(e: Exception, category_slug: str = None):
    if isinstance(e, IntegrityError):
        error_msg = str(e).lower()
        if (
            category_slug is not None
            and "unique constraint" in error_msg
            and "slug" in error_msg
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with slug '{category_slug}' already exists. Please choose a different name.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create category due to a data conflict.",
        )

    if isinstance(e, SQLAlchemyError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unexpected error: {str(e)}",
    )


# Настройка Jinja2
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_categories(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):

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

    if get_user.get("is_admin"):

        return templates.TemplateResponse(
            "categories.html",
            {"request": request, "categories": categories_list, "user": get_user},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbiden"
        )


@router.post("/create", response_class=HTMLResponse)
async def create_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_category: CreateCategory,
    get_user: Annotated[dict, Depends(get_current_user)],
):

    if get_user.get("is_admin"):
        category_slug = slugify(create_category.name)

        if create_category.parent_id is not None:
            parent_check_query = text("SELECT id FROM categories WHERE id = :parent_id")
            parent_result = await db.execute(
                parent_check_query, {"parent_id": create_category.parent_id}
            )

            if parent_result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with ID {create_category.parent_id} does not exist",
                )

        query = text(
            """
            SELECT create_category_function(:category_name, :category_slug, :category_parent_id)
        """
        )

        params = {
            "category_name": create_category.name,
            "category_slug": category_slug,
            "category_parent_id": create_category.parent_id,
        }

        try:
            await db.execute(query, params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            handle_db_error(e, category_slug)

        return JSONResponse(
            content={
                "status_code": status.HTTP_201_CREATED,
                "transaction": "Successful",
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this",
        )


@router.put("/update_category")
async def update_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: int,
    update_category: CreateCategory,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required.",
        )
    print(
        f"Updating category {category_id} with name: {update_category.name} and parent_id: {update_category.parent_id}"
    )

    try:
        check_query = text("SELECT id FROM categories WHERE id = :id")
        id_result = await db.execute(check_query, {"id": category_id})

        existing_category = id_result.scalar_one_or_none()
        if existing_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} does not exist",
            )

        if update_category.parent_id is not None:
            parent_check_query = text(
                "SELECT id, is_active FROM categories WHERE id = :parent_id"
            )
            parent_result = await db.execute(
                parent_check_query, {"parent_id": update_category.parent_id}
            )
            parent = parent_result.one_or_none()

            if parent is None or not parent.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with ID {update_category.parent_id} does not exist or is inactive",
                )

        if update_category.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent",
            )

        category_slug = slugify(update_category.name)

        update_params = {
            "category_id": category_id,
            "category_name": update_category.name,
            "category_parent_id": update_category.parent_id,
            "category_slug": category_slug,
        }

        query = text(
            """
            SELECT update_category_function(:category_id, :category_name, :category_parent_id, :category_slug)
        """
        )

        try:
            await db.execute(query, update_params)
            await db.commit()
        except Exception as e:
            await db.rollback()
            return handle_db_error(e, category_slug)

        return JSONResponse(
            content={
                "status_code": status.HTTP_200_OK,
                "transaction": "Category update successful",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during category update",
        )


@router.delete("/delete")
async def delete_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_admin"):
        check_query = text("SELECT id FROM categories WHERE id = :id")
        id_result = await db.execute(check_query, {"id": category_id})

        existing_category = id_result.scalar_one_or_none()
        if existing_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} does not exist",
            )

        query = text(
            """
            SELECT delete_category_function(:category_id)
        """
        )
        await db.execute(query, {"category_id": category_id})
        await db.commit()

        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Category delete is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be admin user for this",
        )


