from fastapi import APIRouter, Depends, status, HTTPException, Response, Request
from sqlalchemy import select, insert
# from app.models.user import User
from app.schemas import CreateUser
from app.backend.db_depends import get_db
from typing import Annotated
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text
from fastapi.responses import RedirectResponse


SECRET_KEY = '21dbcdc373ff87232b38a5d01ea345426db104960e4ccf5e25da3a4eed608269'
ALGORITHM = 'HS256'
from datetime import datetime, timedelta
from jose import jwt
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")




router = APIRouter(prefix='/auth', tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")




@router.post("/")
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_user: CreateUser
):
    hashed_password = bcrypt_context.hash(create_user.password)

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
        'first_name': create_user.first_name,
        'last_name': create_user.last_name,
        'username': create_user.username,
        'email': create_user.email,
        'hashed_password': hashed_password,
        'is_active': create_user.is_active,
        'is_admin': create_user.is_admin,
        'is_supplier': create_user.is_supplier,
        'is_customer': create_user.is_customer,
    })
    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful"
    }

######################################################################################################### 3



async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    query = text("""
    SELECT id, username, hashed_password, is_active, is_admin, is_supplier, is_customer
    FROM users
    WHERE username = :username
    """)

    result = await db.execute(query, {'username': username})
    user = result.fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
    if not bcrypt_context.verify(password, user.hashed_password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
    return user



######################################################################################################### 1

def get_token(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                             detail='Токен истек')
    return token


async def get_current_user(token: Annotated[str, Depends(get_token)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: str = payload.get('is_admin')
        is_supplier: str = payload.get('is_supplier')
        is_customer: str = payload.get('is_customer')
        expire = payload.get('exp')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )

        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
######################################################################################################### 1

def get_token_optional(request: Request) -> str | None:
    token = request.cookies.get('access_token')
    return token


async def get_current_user_optional(token: Annotated[str, Depends(get_token_optional)]):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: str = payload.get('is_admin')
        is_supplier: str = payload.get('is_supplier')
        is_customer: str = payload.get('is_customer')
        expire = payload.get('exp')
        if username is None or user_id is None:
            return {
            'user': False,
            'username': username,
            'id': user_id,
            'is_admin': False,
            'is_supplier': False,
            'is_customer': False,
            }

        if expire is None:
            return {
            'user': False,
            'username': username,
            'id': user_id,
            'is_admin': False,
            'is_supplier': False,
            'is_customer': False,
            }

        if datetime.now() > datetime.fromtimestamp(expire):
            return {
            'user': False,
            'username': username,
            'id': user_id,
            'is_admin': False,
            'is_supplier': False,
            'is_customer': False,
            }

        return {
            'user': True,
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
        }
    except JWTError:
        return {
            'user': False,
            'username': None,
            'id': None,
            'is_admin': False,
            'is_supplier': False,
            'is_customer': False,
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
######################################################################################################### 4


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin, 'is_supplier': is_supplier, 'is_customer': is_customer}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
######################################################################################################### 2


@router.post('/login')
async def login(response: Response, db: Annotated[AsyncSession, Depends(get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password)
    # if not user or user.is_active == False:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail='Could not validate user'
    #     )

    token = await create_access_token(user.username, user.id, user.is_admin, user.is_supplier, user.is_customer,
                                expires_delta=timedelta(minutes=20))
    
    response.set_cookie(key="access_token", value=token, httponly=False)

    return {'access_token': token,
        'token_type': 'bearer'}

#########################################################################################################

@router.get("/login")
async def get_login_page(request: Request,
                         get_user: Annotated[dict, Depends(get_current_user_optional)]):
    if get_user:  # Если пользователь авторизован
        return RedirectResponse(url="/", status_code=302)  # Перенаправляем на главную
    return templates.TemplateResponse("login.html", {"request": request, "user": get_user})

@router.get("/signup")
async def get_login_page(request: Request,
                         get_user: Annotated[dict, Depends(get_current_user_optional)]):
    if get_user:  # Если пользователь авторизован
        return RedirectResponse(url="/", status_code=302)  # Перенаправляем на главную
    return templates.TemplateResponse("signup.html", {"request": request, "user": get_user})

@router.post("/logout/")
async def logout_user(request: Request):
    request.session.clear()  # Очистить сессию    
    # Удалить cookie авторизации
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")  # Удаляем access_token
    
    return response

@router.get('/read_current_user')
async def read_current_user(request: Request, user: dict = Depends(get_current_user)):
    authenticated = request.cookies.get('access_token') is not None
    return {'User': user, 'isAuthenticated': authenticated}



