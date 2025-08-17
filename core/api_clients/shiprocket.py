# core/api_clients/shiprocket.py
import json
import requests
from django.conf import settings
from orders.models import Order

# Use the robust auth helper (logs in via API User email/password, caches token, refreshes on 401)
from orders.shiprocket_auth import auth_headers, refresh_shiprocket_token


def create_shiprocket_shipment(order: Order, pickup_location: str | None = None) -> dict:
    """
    Create a shipment in Shiprocket for the given order.
    - Uses apiv2 + JWT via orders.shiprocket_auth
    - Auto-refreshes token on 401 and retries once
    - Respects settings.SHIPROCKET_PICKUP_LOCATION (defaults to 'Home')
    """

    pickup = (
        pickup_location
        or getattr(settings, "SHIPROCKET_PICKUP_LOCATION", "Home")
        or "Home"
    )

    # Build items
    items = []
    # If you prefer fewer queries, consider: order.items.select_related("product").all()
    for item in order.items.all():
        p = item.product
        items.append({
            "name": getattr(p, "name", f"Item {p.pk}"),
            "sku": str(getattr(p, "id", "")),
            "units": int(item.quantity),
            "selling_price": float(getattr(item, "price", getattr(p, "price", 0) or 0)),
        })

    if not items:
        raise RuntimeError("Order has no items to send to Shiprocket.")

    payment_method = "Prepaid" if getattr(order, "payment_id", None) else "COD"

    payload = {
        "order_id": str(order.id),
        "order_date": order.order_date.strftime("%Y-%m-%d"),
        "pickup_location": pickup,
        "billing_customer_name": order.name,
        "billing_last_name": "",
        "billing_address": order.address,
        "billing_city": order.city,
        "billing_state": order.state,
        "billing_pincode": order.pincode,
        "billing_country": "India",
        "billing_email": order.email or "",
        "billing_phone": order.phone,
        "shipping_is_billing": True,
        "order_items": items,
        "payment_method": payment_method,
        "sub_total": float(order.total_price),
        # Defaults — adjust as needed or compute from product/cart metadata
        "length": 10,
        "breadth": 10,
        "height": 10,
        "weight": 0.5,
    }

    print("📦 Shiprocket Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    def _call():
        hdrs = auth_headers()  # will ensure a valid JWT (and refresh if cache expired)
        # Safe peek
        auth_val = hdrs.get("Authorization", "")
        peek = (auth_val[:20] + "...") if auth_val else "(missing)"
        print(f"🔐 Using headers: Authorization={peek}, Content-Type={hdrs.get('Content-Type')}")
        return requests.post(
            "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
            headers=hdrs,
            json=payload,
            timeout=30,
        )

    r = _call()

    # If auth problem, refresh once and retry
    if r.status_code == 401:
        print("🔄 Shiprocket 401 — forcing token refresh & retrying once…")
        refresh_shiprocket_token()
        r = _call()

    print("📨 Shiprocket Response:")
    print(r.status_code)
    try:
        print(r.text[:2000])
    except Exception:
        pass

    if r.status_code != 200:
        # raise a readable error back to caller (admin action, signal, etc.)
        raise RuntimeError(f"Shiprocket create failed: {r.text[:400]}")

    try:
        return r.json()
    except Exception:
        return {"raw": r.text}
