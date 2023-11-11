from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    id: str
    title: str
    passenger_capacity: int
    maximum_speed: int
    in_stock: int

class OrderDetail(BaseModel):
    quantity: int
    price: str
    product_id: str
    id: int

class Order(BaseModel):
    order_details: List[OrderDetail] = []
    id: int

class PaginatedOrdersResponse(BaseModel):
    total: int
    pages: int
    current_page: int
    page_size: int
    orders: List[Order]

class CreateOrderDetail(BaseModel):
    product_id: str
    price: float
    quantity: int

class CreateOrder(BaseModel):
    order_details: List[CreateOrderDetail]

class CreateOrderSuccess(BaseModel):
    id: int

class CreateProductSuccess(BaseModel):
    id: str
    
class DeleteProductSuccess(BaseModel):
    id: str