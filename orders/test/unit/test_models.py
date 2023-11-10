from orders.models import Order, OrderDetail
import pytest
from nameko.testing.services import entrypoint_hook

from orders.service import OrdersService
import yaml

from nameko import config as nameko_config
from orders.service import OrdersService

@pytest.fixture
def config():
    return {
        'AMQP_URI': 'pyamqp://guest:guest@localhost',
        'DB_URIS': {"orders:Base": 'postgresql://postgres:postgres@localhost:5432/orders'}
    }

@pytest.fixture
def service_container(container_factory, config):
    container = container_factory(OrdersService, config)
    container.start()
    return container

def test_list_orders(db_session, service_container):
    # Number of orders to test
    num_orders = 3

    for _ in range(num_orders):
        order = Order()
        order_detail_1 = OrderDetail(
            order=order,
            product_id="product1",
            price=100.50,
            quantity=1
        )
        order_detail_2 = OrderDetail(
            order=order,
            product_id="product2",
            price=99.50,
            quantity=2
        )
        db_session.add_all([order, order_detail_1, order_detail_2])

    db_session.commit()

    with entrypoint_hook(service_container, 'list_orders') as list_orders:
        listed_orders = list_orders()

    assert len(listed_orders) > 0
    


def test_can_create_order(db_session):
    order = Order()
    db_session.add(order)
    db_session.commit()
    assert order.id > 0


def test_can_create_order_detail(db_session):
    order = Order()
    order_detail_1 = OrderDetail(
        order=order,
        product_id="the_enigma",
        price=100.50,
        quantity=1
    )
    order_detail_2 = OrderDetail(
        order=order,
        product_id="the_odyssey",
        price=99.50,
        quantity=2
    )

    db_session.add_all([order_detail_1, order_detail_2])
    db_session.commit()

    assert order.id > 0
    for order_detail in order.order_details:
        assert order_detail.id > 0
    assert order_detail_1.product_id == "the_enigma"
    assert order_detail_1.price == 100.50
    assert order_detail_1.quantity == 1
    assert order_detail_2.product_id == "the_odyssey"
    assert order_detail_2.price == 99.50
    assert order_detail_2.quantity == 2
