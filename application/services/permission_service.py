from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.repositories.user_repository import UserRepository
from fastapi import HTTPException, status


class PermissionService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def update_supplier_status(
        self, current_user: dict, user_id: int, db: AsyncSession
    ):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin permission",
            )

        user = await self.user_repo.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_supplier:
            await self.user_repo.update_user(
                user_id, {"is_supplier": False, "is_customer": True}, db
            )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User is no longer supplier",
            }
        else:
            await self.user_repo.update_user(
                user_id, {"is_supplier": True, "is_customer": False}, db
            )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User is now supplier",
            }

    async def delete_or_activate_user(
        self, current_user: dict, user_id: int, db: AsyncSession
    ):
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin permission",
            )

        user = await self.user_repo.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't delete admin user",
            )

        if user.is_active:
            await self.user_repo.update_user(user_id, {"is_active": False}, db)
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User is deleted",
            }
        else:
            await self.user_repo.update_user(user_id, {"is_active": True}, db)
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User is activated",
            }
