from decimal import Decimal
from django.conf import settings
from products.models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """
        Mark the session as "modified" to make sure it gets saved.
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of items in the cart.
        """
        return sum(Decimal(item['price']) * item['quantity'] 
                  for item in self.cart.values())

    def clear(self):
        """
        Remove cart from session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_item_count(self):
        """
        Get the total number of items in the cart.
        """
        return len(self)

    def get_item_total(self, product_id):
        """
        Get the total price for a specific product in the cart.
        """
        product_id = str(product_id)
        if product_id in self.cart:
            return Decimal(self.cart[product_id]['price']) * self.cart[product_id]['quantity']
        return Decimal('0.00')

    def update_quantity(self, product, quantity):
        """
        Update the quantity of a product in the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity > 0:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.remove(product)
            self.save()

    def get_cart_items(self):
        """
        Return a list of cart items with product information.
        """
        items = []
        for item in self:
            items.append({
                'product': item['product'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price']
            })
        return items

    def is_empty(self):
        """
        Check if the cart is empty.
        """
        return len(self.cart) == 0

    def get_total_weight(self):
        """
        Calculate total weight of items in cart (useful for shipping calculations).
        """
        total_weight = 0
        for item in self:
            product = item['product']
            # Assuming weight is stored in kg
            if hasattr(product, 'weight') and product.weight:
                total_weight += product.weight * item['quantity']
        return total_weight