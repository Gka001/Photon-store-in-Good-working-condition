from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0 # Don't show empty lines
    verbose_name_plural = "Products in this Order"

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'order_date', 'status', 'order_items_list']
    list_filter = ['status', 'order_date']    
    inlines = [OrderItemInline]


    def order_items_list(self, obj):
        return ", ".join([
            f"{item.product.name}  (x{item.quantity})"
            for item in obj.items.all()
        ])
    order_items_list.short_description = 'Cart Items'

admin.site.register(Order, OrderAdmin)
#admin.site.register(OrderItem)
