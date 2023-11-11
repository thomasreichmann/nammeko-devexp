from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import DatabaseSession
from sqlalchemy import func

from nameko.events import event_handler

from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail
from orders.schemas import OrderSchema


class OrdersService:
    name = 'orders'

    db = DatabaseSession(DeclarativeBase)
    event_dispatcher = EventDispatcher()
    
    @rpc
    def list_orders(self, page=1, page_size=10):
        total = self.db.query(func.count(Order.id)).scalar()
        orders = self.db.query(Order).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "pages": (total // page_size) + (1 if total % page_size > 0 else 0),
            "current_page": page,
            "page_size": page_size,
            "orders": OrderSchema(many=True).dump(orders).data
        }

    @rpc
    def get_order(self, order_id):
        order = self.db.query(Order).get(order_id)

        if not order:
            raise NotFound('Order with id {} not found'.format(order_id))

        return OrderSchema().dump(order).data

    @rpc
    def create_order(self, order_details):
        order = Order(
            order_details=[
                OrderDetail(
                    product_id=order_detail['product_id'],
                    price=order_detail['price'],
                    quantity=order_detail['quantity']
                )
                for order_detail in order_details
            ]
        )
        self.db.add(order)
        self.db.commit()

        order = OrderSchema().dump(order).data

        self.event_dispatcher('order_created', {
            'order': order,
        })

        return order

    @rpc
    def update_order(self, order):
        order_details = {
            order_details['id']: order_details
            for order_details in order['order_details']
        }

        order = self.db.query(Order).get(order['id'])

        for order_detail in order.order_details:
            order_detail.price = order_details[order_detail.id]['price']
            order_detail.quantity = order_details[order_detail.id]['quantity']

        self.db.commit()
        return OrderSchema().dump(order).data

    @rpc
    def delete_order(self, order_id):
        order = self.db.query(Order).get(order_id)
        self.db.delete(order)
        self.db.commit()
        
    @event_handler("products", "product_deleted")
    def handle_product_deleted(self, payload):
        product_id = payload["product_id"]
        
        order_details_to_delete = self.db.query(OrderDetail).filter(OrderDetail.product_id == product_id)
        order_details_to_delete.delete(synchronize_session=False)
        self.db.commit()

