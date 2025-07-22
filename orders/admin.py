from django.contrib import admin
from .models import Order, OrderItem
import openpyxl
from django.http import HttpResponse
from django.utils.html import format_html

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
        val = self.value()
        if val == '<500':
            return queryset.filter(total_price__lt=500)
        elif val == '500-1000':
            return queryset.filter(total_price__gte=500, total_price__lt=1000)
        elif val == '1000-5000':
            return queryset.filter(total_price__gte=1000, total_price__lt=5000)
        elif val == '>5000':
            return queryset.filter(total_price__gte=5000)
        return queryset

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    verbose_name_plural = "Products in this Order"

def export_as_excel(modeladmin, request, queryset):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['Order ID', 'Customer Name', 'Email', 'Phone', 'Total Price', 'Status', 'Expected Delivery', 'Order Date'])

    for order in queryset:
        sheet.append([
            order.id,
            order.name,
            order.email,
            order.phone,
            float(order.total_price),
            order.status,
            order.expected_delivery.strftime("%Y-%m-%d") if order.expected_delivery else '',
            order.order_date.strftime("%Y-%m-%d %H:%M"),
        ])

    response = HttpResponse(
        content=openpyxl.writer.excel.save_virtual_workbook(workbook),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=orders.xlsx'
    return response
export_as_excel.short_description = "Export Selected Orders to Excel"

def mark_as_shipped(modeladmin, request, queryset):
    updated = queryset.update(status='Shipped')
    modeladmin.message_user(request, f"{updated} order(s) marked as Shipped.")
mark_as_shipped.short_description = "Mark selected orders as Shipped"

def mark_as_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status='Cancelled')
    modeladmin.message_user(request, f"{updated} order(s) marked as Cancelled.")
mark_as_cancelled.short_description = "Mark selected orders as Cancelled"

class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'order_date', 'status', 'expected_delivery',
        'expected_delivery_start', 'expected_delivery_end', 'total_price', 'order_items_list'
    ]
    list_filter = [RealOrderStatusFilter, TotalPriceRangeFilter, 'status', 'order_date']
    list_editable = ['status']
    readonly_fields = ['colored_status', 'expected_delivery', 'expected_delivery_start', 'expected_delivery_end']
    inlines = [OrderItemInline]
    actions = [export_as_excel, mark_as_shipped, mark_as_cancelled]

    def order_items_list(self, obj):
        return ", ".join([f"{item.product.name} (x{item.quantity})" for item in obj.items.all()])
    order_items_list.short_description = 'Cart Items'

    def colored_status(self, obj):
        color = {
            'Pending': 'orange',
            'Shipped': 'blue',
            'Delivered': 'green',
            'Cancelled': 'red',
            'Failed': 'gray',
        }.get(obj.status, 'black')
        return format_html('<strong style="color: {}">{}</strong>', color, obj.status)
    colored_status.short_description = 'Status (Colored)'

    def expected_delivery_start(self, obj):
        return obj.expected_delivery_range[0]
    expected_delivery_start.short_description = "Delivery Start"

    def expected_delivery_end(self, obj):
        return obj.expected_delivery_range[1]
    expected_delivery_end.short_description = "Delivery End"

admin.site.register(Order, OrderAdmin)
