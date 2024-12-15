from fastapi import FastAPI, Depends
from app.routers import category, product, auth, permission, order, review
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request, HTTPException
from fastapi import FastAPI
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    SessionMiddleware, secret_key="7UzGQS7woBazLUtVQJG39ywOP7J7lkPkB0UmDhMgBR8=" # :)
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")


templates = Jinja2Templates(directory="app/templates")



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
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


@app.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request, get_user: Annotated[dict, Depends(get_current_user)]
):
    return templates.TemplateResponse(
        "index.html", {"request": request, "user": get_user}
    )


@app.get("/create_session")
async def session_set(request: Request):
    request.session["my_session"] = "1234"
    return "ok"


@app.get("/read_session")
async def session_info(request: Request):
    my_var = request.session.get("my_session")
    return my_var


@app.get("/delete_session")
async def session_delete(request: Request):
    my_var = request.session.pop("my_session")
    return my_var


app.include_router(auth.router)
app.include_router(category.router)
app.include_router(product.router)
app.include_router(permission.router)
app.include_router(order.router)
app.include_router(review.router)


