from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.presentation.schemas.auth_schema import CreateUser


class UserRepository:
    async def get_user_by_id(self, user_id: int, db: AsyncSession):
        query = text("SELECT * FROM users WHERE id = :user_id")
        result = await db.execute(query, {"user_id": user_id})
        return result.fetchone()

    async def update_user(self, user_id: int, updates: dict, db: AsyncSession):
        set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
        query = text(f"UPDATE users SET {set_clause} WHERE id = :user_id")
        params = {"user_id": user_id, **updates}
        await db.execute(query, params)
        await db.commit()

    async def create_user(self, create_user: CreateUser, hashed_password: str, db: AsyncSession):
        query = text("""
            SELECT create_user_function(
                :first_name, 
                :last_name, 
                :username, 
                :email, 
                :hashed_password, 
                :is_active, 
                :is_admin, 
                :is_supplier, 
                :is_customer
            )
        """)
        await db.execute(query, {
            "first_name": create_user.first_name,
            "last_name": create_user.last_name,
            "username": create_user.username,
            "email": create_user.email,
            "hashed_password": hashed_password,
            "is_active": create_user.is_active,
            "is_admin": create_user.is_admin,
            "is_supplier": create_user.is_supplier,
            "is_customer": create_user.is_customer,
        })
        await db.commit()

    async def get_user_by_username(self, username: str, db: AsyncSession):
        query = text("""
            SELECT id, username, hashed_password, is_active
            FROM users
            WHERE username = :username
        """)
        result = await db.execute(query, {"username": username})
        return result.fetchone()
