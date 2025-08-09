from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from products.models import Product
from .models import CartItem
from django.template.loader import render_to_string

@login_required
def cart_detail(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price for item in cart_items)
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if created:
        cart_item.quantity = 1
    else:
        cart_item.quantity += 1
    cart_item.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": f"{product.name} added to cart.",
        })

    messages.success(request, f"{product.name} added to cart.")
    return redirect('products:product_list')

@login_required
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    CartItem.objects.filter(user=request.user, product=product).delete()
    messages.info(request, f"{product.name} removed from cart.")
    return redirect('cart:cart_detail')

@login_required
def cart_increase(request, product_id):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    cart_item.quantity += 1
    cart_item.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        cart_items = CartItem.objects.filter(user=request.user)
        cart_total = sum(item.total_price for item in cart_items)
        return JsonResponse({
            'quantity': cart_item.quantity,
            'item_total': float(cart_item.total_price),
            'cart_total': float(cart_total),
        })

    return redirect('cart:cart_detail')

@login_required
def cart_decrease(request, product_id):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        quantity = cart_item.quantity
        item_total = cart_item.total_price
    else:
        cart_item.delete()
        quantity = 0
        item_total = 0

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        cart_items = CartItem.objects.filter(user=request.user)
        cart_total = sum(item.total_price for item in cart_items)
        return JsonResponse({
            'quantity': quantity,
            'item_total': float(item_total),
            'cart_total': float(cart_total),
        })

    return redirect('cart:cart_detail')

@login_required
def cart_mini_preview(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.total_price for item in cart_items)
    html = render_to_string('cart/_mini_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })
    return JsonResponse({'html': html})

@login_required
def cart_count_view(request):
    count = 0
    if request.user.is_authenticated:
        count = sum(item.quantity for item in CartItem.objects.filter(user=request.user))
    return JsonResponse({"cart_count": count})
