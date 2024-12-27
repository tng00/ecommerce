from fastapi.exceptions import RequestValidationError
from app.routers import category, product, auth, permission, order, review, cart,search
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, status, Depends, Request, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from app.routers.auth import get_current_user, get_current_user_optional
from typing import Annotated


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="7UzGQS7woBazLUtVQJG39ywOP7J7lkPkB0UmDhMgBR8=")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        # Логика редиректа на главную страницу
        return RedirectResponse(url="/")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Логика для перенаправления на главную страницу при ошибке 422
    return RedirectResponse(url="/")

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    if (
        exc.status_code == status.HTTP_403_FORBIDDEN
        or exc.status_code == status.HTTP_401_UNAUTHORIZED
    ):
        return templates.TemplateResponse(
            "access_denied.html",
            {
                "request": request,
                "user": {
                    "is_admin": False,
                    "is_supplier": False,
                    "is_customer": False,
                },
            },
        )
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        # Редирект на главную страницу для 404 ошибки
        return RedirectResponse(url="/")
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


app.include_router(auth.router)
app.include_router(category.router)
app.include_router(product.router)
app.include_router(permission.router)
app.include_router(order.router)
app.include_router(review.router)
app.include_router(cart.router)
app.include_router(search.router)

@app.get("/", include_in_schema=False)
async def redirect_to_search():
    return RedirectResponse(url="/search/")
