from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from starlette import status
from .auth import get_current_user
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


router = APIRouter(prefix='/permission', tags=['permission'])


@router.patch('/')
async def supplier_permission(
    db: Annotated[AsyncSession, Depends(get_db)], 
    get_user: Annotated[dict, Depends(get_current_user)],
    user_id: int
):
    if get_user.get('is_admin'):
        query = text("""
            SELECT * FROM users WHERE id = :user_id
        """)
        result = await db.execute(query, {'user_id': user_id})
        user = result.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )

        if user.is_supplier:
            update_query = text("""
                UPDATE users
                SET is_supplier = FALSE, is_customer = TRUE
                WHERE id = :user_id
            """)
            await db.execute(update_query, {'user_id': user_id})
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is no longer supplier'
            }
        else:
            update_query = text("""
                UPDATE users
                SET is_supplier = TRUE, is_customer = FALSE
                WHERE id = :user_id
            """)
            await db.execute(update_query, {'user_id': user_id})
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is now supplier'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission"
        )
    


@router.delete('/delete')
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)], 
    get_user: Annotated[dict, Depends(get_current_user)], 
    user_id: int
):
    if get_user.get('is_admin'):
        query = text("""
            SELECT * FROM users WHERE id = :user_id
        """)
        result = await db.execute(query, {'user_id': user_id})
        user = result.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't delete admin user"
            )

        if user.is_active:
            update_query = text("""
                UPDATE users
                SET is_active = FALSE
                WHERE id = :user_id
            """)
            await db.execute(update_query, {'user_id': user_id})
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is deleted'
            }
        else:
            update_query = text("""
                UPDATE users
                SET is_active = TRUE
                WHERE id = :user_id
            """)
            await db.execute(update_query, {'user_id': user_id})
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is activated'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission"
        )