from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db import engine
from app.backend.db_depends import get_db
from sqlalchemy import text

from app.schemas import CreateReview
from app.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse


router = APIRouter(prefix="/review", tags=["review"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_active_reviews(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    try:
        if (get_user.get("is_customer")):
            query = text("SELECT * FROM get_active_reviews() WHERE user_id = :user_id")
        else:
            query = text("SELECT * FROM get_active_reviews()")
        result = await db.execute(query, {"user_id": get_user.get("id")})
        reviews = result.fetchall()
        reviews_list = [
            {
                "id": review.id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "rating": review.rating,
                "comment": review.comment,
                "product_name": review.product_name
            }
            for review in reviews
        ]

        return templates.TemplateResponse(
            "review.html",
            {"request": request, "reviews": reviews_list, "user": get_user},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )



@router.post("/create")
async def create_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_review: CreateReview,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get("is_customer") or get_user.get("is_admin"):
        user_id = int(get_user.get("id"))
        product_id = create_review.product_id

        query = text(
            """
            SELECT id FROM reviews WHERE user_id = :user_id AND product_id = :product_id
            """
        )
        result = await db.execute(query, {"user_id": user_id, "product_id": product_id})
        existing_review = result.scalars().first()

        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already left a review for this product."
            )

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
        await db.execute(
            query,
            {
                "review_product_id": create_review.product_id,
                "review_user_id": user_id,
                "review_rating": create_review.rating,
                "review_comment": create_review.comment,
            },
        )
        await db.commit()

        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )
