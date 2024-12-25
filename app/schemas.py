from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: int

class CreateOrder(BaseModel):
    address: str
    is_card: bool
    is_sbp: bool
    items: List[OrderItem]
    total: int

class OrderUpdate(BaseModel):
    status: str

class CreatePayment(BaseModel):
    date: date
    is_card: bool
    is_sbp: bool

class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    stock: int = Field(ge=0)
    category: int

class CreateReview(BaseModel):
    product_id: int
    rating: int
    comment: str

class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int

class CreateCategory(BaseModel):
    name: str
    parent_id: Optional[int] = None


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    is_active: bool = True
    is_admin: bool = False
    is_supplier: bool = False
    is_customer: bool = False


class CreateCheck(BaseModel):
    item: str
    price: int