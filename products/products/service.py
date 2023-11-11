import logging

from nameko.events import event_handler
from nameko.rpc import rpc
from nameko.events import EventDispatcher

from products import dependencies, schemas


logger = logging.getLogger(__name__)


class ProductsService:

    name = 'products'

    storage = dependencies.Storage()
    
    event_dispatcher = EventDispatcher()

    @rpc
    def get(self, product_id):
        product = self.storage.get(product_id)
        return schemas.Product().dump(product).data
    
    @rpc
    def delete(self, product_id):
        self.storage.delete(product_id)
        self.event_dispatcher("product_deleted", {"product_id": product_id})

    @rpc
    def list(self):
        products = self.storage.list()
        print(len(products))
        return schemas.Product(many=True).dump(products).data

    @rpc
    def create(self, product):
        product = schemas.Product(strict=True).load(product).data
        self.storage.create(product)
        
    @rpc
    def get_products_by_ids(self, product_ids):
        products = self.storage.get_products_by_ids(product_ids)
        return schemas.Product(many=True).dump(products).data

    @event_handler('orders', 'order_created')
    def handle_order_created(self, payload):
        for product in payload['order']['order_details']:
            self.storage.decrement_stock(
                product['product_id'], product['quantity'])
