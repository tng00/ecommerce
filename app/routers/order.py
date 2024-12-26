from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db import engine
from app.backend.db_depends import get_db
from sqlalchemy import select, insert, update, text

from app.schemas import CreateOrder, OrderUpdate, CreateCheck
from app.routers.auth import get_current_user 
#from app.routers.cart import update_cart, get_cart_quantities
from fastapi.templating import Jinja2Templates
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse,
    StreamingResponse,
)
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

from yookassa import Configuration, Payment
import uuid

idempotence_key = str(uuid.uuid4())
Configuration.account_id = "1005331"
Configuration.secret_key = "test_JE0B3RMdXgc_KdjzMj-aIdLdJW-cANg1KC2pgUR_xd0"#потом не забыть спрятать в env.



CHECKS_DIR = "app/static/checks"
os.makedirs(CHECKS_DIR, exist_ok=True)


router = APIRouter(prefix="/order", tags=["order"])


# Настройка Jinja2
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_all_orders(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_current_user)],
):
    try:
        if get_user.get("is_admin"):
            query = text("SELECT * FROM get_all_orders() ORDER BY id desc")
            result = await db.execute(query)
        elif get_user.get("is_supplier"):
            user_id = get_user.get("id")
            query = text(
                """
                SELECT oi.*
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE p.supplier_id = :user_id
                ORDER BY id desc
                """
            )
            result = await db.execute(query, {"user_id": user_id})
            orders = result.fetchall()

            orders_list = [
                {
                    "id": order.id,
                    "order_id": order.order_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "price": order.price,
                }
                for order in orders
            ]

            return templates.TemplateResponse(
                "order.html",
                {"request": request, "orders": orders_list, "user": get_user},
            )
        elif get_user.get("is_customer"):
            user_id = get_user.get("id")
            query = text("SELECT * FROM get_all_orders() WHERE user_id = :user_id ORDER BY id desc")
            result = await db.execute(query, {"user_id": user_id})

        orders = result.fetchall()
        orders_list = [
            {
                "id": order.id,
                "user_id": order.user_id,
                "payment_id": order.payment_id,
                "order_date": order.order_date,
                "address": order.address,
                "total": order.total,
                "status": order.status,
            }
            for order in orders
        ]

        return templates.TemplateResponse(
            "order.html",
            {"request": request, "orders": orders_list, "user": get_user},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{order_id}/", response_class=HTMLResponse)
async def get_product_detail(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    order_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    try:
        query = text("SELECT * FROM order_items WHERE order_id = :id")
        result = await db.execute(query, {"id": order_id})
        order_items = result.fetchall()
        order_items_detail = [
            {
                "order_id": order_item.order_id,
                "product_id": order_item.product_id,
                "quantity": order_item.quantity,
                "price": order_item.price,
            }
            for order_item in order_items
        ]

        query = text("SELECT * FROM orders WHERE id = :id")
        result = await db.execute(query, {"id": order_id})
        order = result.fetchone()
        order_detail = [{
            "id": order.id,
            "order_date": order.order_date,
            "address": order.address,
            "total": order.total,
            "status": order.status
        }]


        return templates.TemplateResponse(
            "order_page.html",
            {"request": request, "order": order_detail ,"order_items": order_items_detail, "user": get_user},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

# @router.get("/check/{check_id}")
# async def get_check(check_id: str):
#     check_file_path = os.path.join(CHECKS_DIR, f"{check_id}.pdf")
#     if not os.path.exists(check_file_path):
#         raise HTTPException(status_code=404, detail="Check not found")

#     return RedirectResponse(url=f"/static/checks/{check_id}.pdf")




# @router.post("/create")
# async def create_order(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     create_order: CreateOrder,
#     get_user: Annotated[dict, Depends(get_current_user)],
# ):

    if get_user.get("is_customer") or get_user.get("is_admin"):
        user_id = get_user.get("id")
        current_timestamp = datetime.now()
        query = text(
            """
                SELECT create_order(:is_card, :is_sbp, :user_id, :order_date, :address, :total)
            """
        )
        result = await db.execute(
            query,
            {
                "is_card": create_order.is_card,
                "is_sbp": create_order.is_sbp,
                "user_id": user_id,
                "order_date": current_timestamp,
                "address": create_order.address,
                "total": create_order.total,
            },
        )
        order_id = result.scalar()
        print(order_id)
        await db.commit()
        
        for item in create_order.items:
            query = text(
                """
                INSERT INTO order_items(order_id, product_id, quantity, price)
                VALUES (:order_id, :product_id, :quantity, :price)
            """
            )
            await db.execute(
                query,
                {
                    "order_id": order_id,
                    "product_id": int(item.product_id),
                    "quantity": item.quantity,
                    "price": item.price,
                },
            )
            await db.commit()

        check_id = str(uuid.uuid4())
        check_file_path = os.path.join(CHECKS_DIR, f"{check_id}.pdf")
        total_amount = sum(item.quantity * item.price for item in create_order.items)
        payment = Payment.create({
                "amount": {
                    "value": str(total_amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://www.example.com/return_url"
                },
                "capture": True,
                "description": "Заказ №" + str(order_id) 
            }, uuid.uuid4())

        #print(f"ID: {payment.id}")
        #print(f"Status: {payment.status}")
        #print(f"Paid: {payment.paid}")
        #print(f"Amount: {payment.amount.value} {payment.amount.currency}")
        #print(f"Confirmation Type: {payment.confirmation.type}")
        #print(f"Confirmation URL: {payment.confirmation.confirmation_url}")
        #print(f"Created At: {payment.created_at}")
        #print(f"Description: {payment.description}")
        #print(f"Metadata: {payment.metadata}")
        #print(f"Recipient Account ID: {payment.recipient.account_id}")
        #print(f"Recipient Gateway ID: {payment.recipient.gateway_id}")
        #print(f"Refundable: {payment.refundable}")
        #print(f"Test: {payment.test}")
 
        return JSONResponse(content={"payment_url": payment.confirmation.confirmation_url})
       



@router.post("/create")
async def create_order(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_order: CreateOrder,
    get_user: Annotated[dict, Depends(get_current_user)],
):

    if get_user.get("is_customer") or get_user.get("is_admin"):
        user_id = get_user.get("id")
        current_timestamp = datetime.now()
        query = text(
            """
                SELECT create_order(:is_card, :is_sbp, :user_id, :order_date, :address, :total)
            """
        )
        result = await db.execute(
            query,
            {
                "is_card": create_order.is_card,
                "is_sbp": create_order.is_sbp,
                "user_id": user_id,
                "order_date": current_timestamp,
                "address": create_order.address,
                "total": create_order.total,
            },
        )
        order_id = result.scalar()
        print(order_id)
        await db.commit()
        
        for item in create_order.items:
            query = text(
                """
                INSERT INTO order_items(order_id, product_id, quantity, price)
                VALUES (:order_id, :product_id, :quantity, :price)
            """
            )
            await db.execute(
                query,
                {
                    "order_id": order_id,
                    "product_id": int(item.product_id),
                    "quantity": item.quantity,
                    "price": item.price,
                },
            )
            await db.commit()

        check_id = str(uuid.uuid4())
        check_file_path = os.path.join(CHECKS_DIR, f"{check_id}.pdf")

        total_amount = sum(item.quantity * item.price for item in create_order.items)
        payment = Payment.create({
                "amount": {
                    "value": str(total_amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://www.example.com/return_url"
                },
                "capture": True,
                "description": "Заказ №" + str(order_id) 
            }, uuid.uuid4())

        #print(f"ID: {payment.id}")
        #print(f"Status: {payment.status}")
        #print(f"Paid: {payment.paid}")
        #print(f"Amount: {payment.amount.value} {payment.amount.currency}")
        #print(f"Confirmation Type: {payment.confirmation.type}")
        #print(f"Confirmation URL: {payment.confirmation.confirmation_url}")
        #print(f"Created At: {payment.created_at}")
        #print(f"Description: {payment.description}")
        #print(f"Metadata: {payment.metadata}")
        #print(f"Recipient Account ID: {payment.recipient.account_id}")
        #print(f"Recipient Gateway ID: {payment.recipient.gateway_id}")
        #print(f"Refundable: {payment.refundable}")
        #print(f"Test: {payment.test}")
 
        return JSONResponse(content={"payment_url": payment.confirmation.confirmation_url})
       

@router.put("/update/{order_id}")
async def update_order(
    db: Annotated[AsyncSession, Depends(get_db)],
    order_id: int,
    order_update: OrderUpdate,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    query = text(
        """
        SELECT * FROM orders WHERE id = :id
        """
    )
    result = await db.execute(query, {"id": order_id})
    order = result.fetchone()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There is no order found"
        )

    if get_user.get("is_admin"):
        update_query = text(
            """
            UPDATE orders SET status = :status WHERE id = :id
            """
        )
        await db.execute(
            update_query,
            {
                "status": order_update.status,
                "id": order_id,
            },
        )
        await db.commit()

        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "Order update is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this order",
        )





# @router.post("/create")
# async def create_order(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     create_order: CreateOrder,
#     get_user: Annotated[dict, Depends(get_current_user)],
# ):
#     user_id = validate_user_access(get_user)
#     current_timestamp = datetime.now()

#     try:
#         # Шаг 1: Создаем заказ
#         order_id = await create_order_in_db(db, user_id, create_order, current_timestamp)
#         await db.commit()

#         # Шаг 2: Добавляем товары в заказ
#         await add_order_items(db, order_id, create_order.items)
#         await db.commit()

#         # Шаг 3: Генерируем check_id и обновляем заказ
#         check_id = str(uuid.uuid4())
#         await update_order_with_check_id(db, order_id, check_id)
#         await db.commit()

#         return {"order_id": order_id, "check_url": f"/order/check/{check_id}"}

#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e),
#         )
