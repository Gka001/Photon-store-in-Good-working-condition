from .models import CartItem
from products.models import Product

def get_user_cart(user):
    return CartItem.objects.filter(user=user).select_related('product')

def add_to_user_cart(user, product_id, quantity=1):
    product = Product.objects.get(id=product_id)
    item, created = CartItem.objects.get_or_create(user=user, product=product)
    if not created:
        item.quantity += quantity
    item.save()

def remove_from_user_cart(user, product_id):
    CartItem.objects.filter(user=user, product_id=product_id).delete()

def update_user_cart_quantity(user, product_id, delta):
    item = CartItem.objects.filter(user=user, product_id=product_id).first()
    if item:
        item.quantity += delta
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

def get_user_cart_total(user):
    return sum(item.total_price for item in get_user_cart(user))
