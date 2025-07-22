from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order_success/', views.order_success, name='order_success'),
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
    path('order_history/', views.order_history, name='order_history'),
    path('create_razorpay_order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('razorpay_payment/', views.razorpay_payment, name='razorpay_payment'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
]
