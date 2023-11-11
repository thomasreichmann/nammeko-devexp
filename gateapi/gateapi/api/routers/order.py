from os import name
from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from typing import List
from gateapi.api import schemas
from fastapi import Query
from gateapi.api.dependencies import get_rpc, config
from .exceptions import OrderNotFound, ProductNotFound

router = APIRouter(
    prefix = "/orders",
    tags = ['Orders']
)


@router.get("", status_code=status.HTTP_200_OK)
def list_orders(
    page: int = Query(1, alias="page", ge=1),
    page_size: int = Query(10, alias="page_size", ge=1),
    rpc = Depends(get_rpc)
):
    with rpc.next() as nameko:
        return nameko.orders.list_orders(page, page_size)


@router.get("/{order_id}", status_code=status.HTTP_200_OK)
def get_order(order_id: int, rpc = Depends(get_rpc)):
    try:
        return _get_order(order_id, rpc)
    except OrderNotFound as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

def _get_order(order_id, nameko_rpc):
    # Retrieve order data from the orders service
    with nameko_rpc.next() as nameko:
        order = nameko.orders.get_order(order_id)

    # Extract product IDs from the order
    product_ids = [item['product_id'] for item in order['order_details']]

    # Fetch details for these products
    with nameko_rpc.next() as nameko:
        products = nameko.products.get_products_by_ids(product_ids)
        product_map = {prod['id']: prod for prod in products}

    # get the configured image root
    image_root = config['PRODUCT_IMAGE_ROOT']

    # Enhance order details with product and image details
    for item in order['order_details']:
        product_id = item['product_id']
        product = product_map.get(product_id, {})

        item['product'] = product
        # Construct an image URL and add it to the item
        item['image'] = '{}/{}.jpg'.format(image_root, product_id)

    return order

@router.post("", status_code=status.HTTP_200_OK, response_model=schemas.CreateOrderSuccess)
def create_order(request: schemas.CreateOrder, rpc = Depends(get_rpc)):
    id_ =  _create_order(request.dict(), rpc)
    return {
        'id': id_
    }

def _create_order(order_data, nameko_rpc):
    # Extract product IDs from the order details
    product_ids = [item['product_id'] for item in order_data['order_details']]

    try:
        # Fetch product details for the given IDs
        with nameko_rpc.next() as nameko:
            products = nameko.products.get_products_by_ids(product_ids)

        # Validate if all product IDs are valid
        if len(products) != len(product_ids):
            # Handle invalid product IDs
            missing_ids = set(product_ids) - {prod['id'] for prod in products}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Products with IDs {missing_ids} not found")

        # Proceed with order creation
        result = nameko.orders.create_order(order_data['order_details'])
        return result['id']

    except ProductNotFound as e:
        # Handle the ProductNotFound exception
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
