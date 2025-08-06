from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('mini-preview/', views.cart_mini_preview, name='cart_mini_preview'),
    path('increase/<int:product_id>/', views.cart_increase, name='cart_increase'),
    path('decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    path('cart-count/', views.cart_count, name='cart_count'),
]
