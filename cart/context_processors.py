from .models import CartItem
from .utils import get_user_cart_total

def cart_item_count(request):
    cart_count = 0
    total_price = 0.0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        cart_count = sum(item.quantity for item in cart_items)
        total_price = sum(item.get_total_price() for item in cart_items)
    return {
        'cart_count': cart_count,
        'total_price': total_price,
    }
