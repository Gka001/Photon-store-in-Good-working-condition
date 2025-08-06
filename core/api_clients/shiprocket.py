import requests
from django.conf import settings
from orders.models import Order
import json


def create_shiprocket_shipment(order: Order):
    token = settings.SHIPROCKET_API_TOKEN

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
        "pickup_location": "Home",  # Make sure this matches the location name in Shiprocket
        "billing_customer_name": order.name,
        "billing_last_name": "",
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

    print("📦 Shiprocket Payload:")
    print(json.dumps(payload, indent=2))

    response = requests.post(
        "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
        headers=headers,
        json=payload,
    )

    print("📨 Shiprocket Response:")
    print(response.status_code)
    print(response.text)

    response.raise_for_status()
    return response.json()
