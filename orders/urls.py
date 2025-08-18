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
    path('create_razorpay_order_reserved/', views.create_razorpay_order_reserved, name='create_razorpay_order_reserved'),
    path('razorpay_finalize_reserved/', views.razorpay_finalize_reserved, name='razorpay_finalize_reserved'),
    path('release_pending_order/', views.release_pending_order, name='release_pending_order'),

]
