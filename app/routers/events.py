
# from typing import Annotated
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import select, update
# from starlette import status
# from .auth import get_current_user
# from sqlalchemy.orm import Session
# from app.backend.db_depends import get_db
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import text


# router = APIRouter(prefix='/events', tags=['events'])


# @router.post("/view")
# async def track_view(
#     user_id: int, product_id: int, db: Annotated[AsyncSession, Depends(get_db)]
# ):
#     """
#     Запись события просмотра товара.
#     """
#     query = text("""
#         INSERT INTO user_events (user_id, event_type, product_id)
#         VALUES (:user_id, 'view', :product_id)
#     """)
#     await db.execute(query, {"user_id": user_id, "product_id": product_id})
#     await db.commit()
#     return {"status": "success", "message": "View event recorded"}


# @router.post("/add_to_cart")
# async def track_add_to_cart(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     user_id: int,
#     product_id: int,
#     quantity: int = 1,
# ):
#     """
#     Запись события добавления товара в корзину.
#     """
#     query = text("""
#         INSERT INTO user_events (user_id, event_type, product_id, quantity)
#         VALUES (:user_id, 'add_to_cart', :product_id, :quantity)
#     """)
#     await db.execute(query, {"user_id": user_id, "product_id": product_id, "quantity": quantity})
#     await db.commit()
#     return {"status": "success", "message": "Add to cart event recorded"}



# @router.post("/purchase")
# async def track_purchase(
#     user_id: int,
#     product_id: int,
#     quantity: int,
#     total_amount: float,
#     db: Annotated[AsyncSession, Depends(get_db)],
# ):
#     """
#     Запись события покупки товара.
#     """
#     query = text("""
#         INSERT INTO user_events (user_id, event_type, product_id, quantity, metadata)
#         VALUES (:user_id, 'purchase', :product_id, :quantity, :metadata)
#     """)
#     metadata = {"total_amount": total_amount}
#     await db.execute(
#         query, {"user_id": user_id, "product_id": product_id, "quantity": quantity, "metadata": metadata}
#     )
#     await db.commit()
#     return {"status": "success", "message": "Purchase event recorded"}


# @router.post("/review")
# async def track_review(
#     user_id: int,
#     product_id: int,
#     rating: int,
#     comment: str,
#     db: Annotated[AsyncSession, Depends(get_db)],
# ):
#     """
#     Запись события отзыва на товар.
#     """
#     query = text("""
#         INSERT INTO user_events (user_id, event_type, product_id, metadata)
#         VALUES (:user_id, 'review', :product_id, :metadata)
#     """)
#     metadata = {"rating": rating, "comment": comment}
#     await db.execute(query, {"user_id": user_id, "product_id": product_id, "metadata": metadata})
#     await db.commit()
#     return {"status": "success", "message": "Review event recorded"}


