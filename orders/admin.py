from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.conf import settings
import openpyxl
import json

from .models import Order, OrderItem

# Use the unified client
from core.api_clients.shiprocket import create_shiprocket_shipment


class RealOrderStatusFilter(admin.SimpleListFilter):
    title = 'Real Orders Only'
    parameter_name = 'real'

    def lookups(self, request, model_admin):
        return [('yes', 'Only Paid Orders')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(payment_id__isnull=True).exclude(payment_id__exact='')


class TotalPriceRangeFilter(admin.SimpleListFilter):
    title = 'Total Price Range'
    parameter_name = 'total_price_range'

    def lookups(self, request, model_admin):
        return [
            ('<500', 'Below ₹500'),
            ('500-1000', '₹500 - ₹1000'),
            ('1000-5000', '₹1000 - ₹5000'),
            ('>5000', 'Above ₹5000'),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == '<500':
            return queryset.filter(total_price__lt=500)
        if v == '500-1000':
            return queryset.filter(total_price__gte=500, total_price__lt=1000)
        if v == '1000-5000':
            return queryset.filter(total_price__gte=1000, total_price__lt=5000)
        if v == '>5000':
            return queryset.filter(total_price__gte=5000)
        return queryset


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    verbose_name_plural = "Products in this Order"


def export_as_excel(modeladmin, request, queryset):
    wb = openpyxl.Workbook()
    sh = wb.active
    sh.append(['Order ID', 'Customer Name', 'Email', 'Phone', 'Total Price', 'Status', 'Expected Delivery', 'Order Date'])

    for order in queryset:
        sh.append([
            order.id,
            order.name,
            order.email,
            order.phone,
            float(order.total_price),
            order.status,
            order.expected_delivery.strftime("%Y-%m-%d") if getattr(order, "expected_delivery", None) else '',
            order.order_date.strftime("%Y-%m-%d %H:%M"),
        ])

    resp = HttpResponse(
        content=openpyxl.writer.excel.save_virtual_workbook(wb),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = 'attachment; filename=orders.xlsx'
    return resp
export_as_excel.short_description = "Export Selected Orders to Excel"


def _push_to_shiprocket(order: Order):
    # Validate minimal fields
    required = [order.name, order.address, order.city, order.state, order.pincode, order.phone]
    if not all(required):
        raise RuntimeError("Order missing address fields (name/address/city/state/pincode/phone).")

    # Build items (reuse related)
    items = []
    for oi in order.items.select_related("product").all():
        p = oi.product
        items.append({
            "name": getattr(p, "name", f"Item {p.pk}"),
            "sku": str(getattr(p, "id", "")),
            "units": int(oi.quantity),
            "selling_price": float(getattr(oi, "price", getattr(p, "price", 0) or 0)),
        })
    if not items:
        raise RuntimeError("Order has no items to send to Shiprocket.")

    # Prepare payload (the client prints payload & response already)
    payment_method = "Prepaid" if getattr(order, "payment_id", None) else "COD"
    payload_like = {
        "order_id": str(order.id),
        "order_date": order.order_date.strftime("%Y-%m-%d"),
        "pickup_location": getattr(settings, "SHIPROCKET_PICKUP_LOCATION", "Home") or "Home",
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
        "length": 10, "breadth": 10, "height": 10, "weight": 0.5,
    }

    # Call the unified client (handles auth + 401 retry)
    resp = create_shiprocket_shipment(order, pickup_location=payload_like["pickup_location"])

    # Persist useful IDs if present
    changed = False
    if hasattr(order, "shiprocket_order_id") and resp.get("order_id"):
        order.shiprocket_order_id = str(resp["order_id"]); changed = True
    if hasattr(order, "shiprocket_shipment_id") and resp.get("shipment_id"):
        order.shiprocket_shipment_id = str(resp["shipment_id"]); changed = True
    if hasattr(order, "awb_code") and resp.get("awb_code"):
        order.awb_code = str(resp["awb_code"]); changed = True
    if hasattr(order, "tracking_url") and resp.get("tracking_url"):
        order.tracking_url = resp["tracking_url"]; changed = True

    if changed:
        order.save()
    return resp


def mark_as_shipped(modeladmin, request, queryset):
    updated, pushed = 0, 0
    for order in queryset:
        if order.status != 'Shipped':
            order.status = 'Shipped'
            order.save(update_fields=["status"])
            updated += 1
        try:
            _push_to_shiprocket(order)
            pushed += 1
        except Exception as e:
            messages.error(request, f"Order #{order.id}: Failed to push to Shiprocket: {e}")
    modeladmin.message_user(request, f"{updated} updated, {pushed} pushed to Shiprocket.")
mark_as_shipped.short_description = "Mark selected orders as Shipped (and push)"


def mark_as_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status='Cancelled')
    modeladmin.message_user(request, f"{updated} cancelled.")
mark_as_cancelled.short_description = "Mark selected orders as Cancelled"


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'order_date', 'status', 'expected_delivery', 'total_price', 'order_items_list']
    list_filter = [RealOrderStatusFilter, TotalPriceRangeFilter, 'status', 'order_date']
    list_editable = ['status']
    readonly_fields = ['colored_status', 'expected_delivery']
    inlines = [OrderItemInline]
    actions = [export_as_excel, mark_as_shipped, mark_as_cancelled]

    def order_items_list(self, obj):
        return ", ".join([f"{item.product.name} (x{item.quantity})" for item in obj.items.all()])

    def colored_status(self, obj):
        color = {'Pending': 'orange','Shipped': 'blue','Delivered': 'green','Cancelled': 'red','Failed': 'gray'}.get(obj.status, 'black')
        return format_html('<strong style="color:{}">{}</strong>', color, obj.status)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)  # optional
