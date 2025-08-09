from .models import CartItem

def cart_count(request):
    if request.user.is_authenticated:
        count = sum(item.quantity for item in CartItem.objects.filter(user=request.user))
    else:
        count = 0
    return {'cart_count': count}
