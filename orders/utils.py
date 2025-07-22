from datetime import timedelta
from django.utils import timezone
from .models import Order

def get_delivery_range(order):
    if not isinstance(order, Order):
        return None, None

    today = timezone.now().date()
    if "metro" in order.address.lower():
        return today + timedelta(days=7), today + timedelta(days=10)
    else:
        return today + timedelta(days=10), today + timedelta(days=14)
