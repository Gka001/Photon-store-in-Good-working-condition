import requests
from django.conf import settings
from orders.models import Order


def get_shiprocket_token():
    url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    payload = {
        "email": settings.SHIPROCKET_EMAIL,
        "password": settings.SHIPROCKET_PASSWORD,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("token")


def create_shiprocket_shipment(order: Order):
    token = get_shiprocket_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    items = []
    for item in order.items.all():
        items.append({
            "name": item.product.name,
            "sku": str(item.product.id),
            "units": item.quantity,
            "selling_price": float(item.product.price),
        })

    payload = {
        "order_id": str(order.id),
        "order_date": order.order_date.strftime("%Y-%m-%d"),
        "pickup_location": "Primary",  # Make sure this matches the location name in Shiprocket
        "billing_customer_name": order.name,
        "billing_address": order.address,
        "billing_city": order.city,
        "billing_state": order.state,
        "billing_pincode": order.pincode,
        "billing_country": "India",
        "billing_email": order.email,
        "billing_phone": order.phone,
        "shipping_is_billing": True,
        "order_items": items,
        "payment_method": "Prepaid" if order.payment_id else "COD",
        "sub_total": float(order.total_price),
        "length": 10,
        "breadth": 10,
        "height": 10,
        "weight": 0.5,
    }

    response = requests.post(
        "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    return response.json()
