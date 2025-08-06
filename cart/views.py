from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from products.models import Product
from .models import CartItem
from .utils import get_user_cart, get_user_cart_total


def get_cart_items(request):
    return get_user_cart(request.user)


@require_POST
@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override') == 'true'

    item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        new_quantity = quantity if override else item.quantity + quantity
    else:
        new_quantity = quantity

    if new_quantity > product.stock:
        message = f"Only {product.stock} items of '{product.name}' in stock."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': message})
        messages.error(request, message)
        return redirect('products:product_detail', slug=product.slug)

    item.quantity = new_quantity
    item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_count = get_user_cart(request.user).count()
        return JsonResponse({'status': 'success', 'message': 'Added to cart', 'cart_count': cart_count})

    return redirect('cart:cart_detail')


@require_POST
@login_required
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    CartItem.objects.filter(user=request.user, product=product).delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = get_cart_items(request)
        total_price = get_user_cart_total(request.user)
        html = render_to_string('cart/_mini_cart.html', {'cart_items': items, 'total_price': total_price}, request=request)
        cart_count = items.count()
        return JsonResponse({'status': 'success', 'message': 'Item removed', 'html': html, 'cart_count': cart_count})

    return redirect('cart:cart_detail')


@login_required
def cart_detail(request):
    items = get_cart_items(request)
    total_price = get_user_cart_total(request.user)
    return render(request, 'cart/cart.html', {'cart_items': items, 'total_price': total_price})


@login_required
def cart_mini_preview(request):
    items = get_cart_items(request)
    total_price = get_user_cart_total(request.user)
    html = render_to_string('cart/_mini_cart.html', {'cart_items': items, 'total_price': total_price}, request=request)
    return JsonResponse({'html': html})


@require_POST
@login_required
def cart_increase(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        item = CartItem.objects.get(user=request.user, product=product)
        if item.quantity + 1 <= product.stock:
            item.quantity += 1
            item.save()
        else:
            messages.error(request, f"Cannot increase. Only {product.stock} in stock.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in cart.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = get_cart_items(request)
        total_price = get_user_cart_total(request.user)
        html = render_to_string('cart/_mini_cart.html', {'cart_items': items, 'total_price': total_price}, request=request)
        cart_count = items.count()
        return JsonResponse({'status': 'success', 'message': 'Quantity increased', 'html': html, 'cart_count': cart_count})

    return redirect('cart:cart_detail')


@require_POST
@login_required
def cart_decrease(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        item = CartItem.objects.get(user=request.user, product=product)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in cart.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = get_cart_items(request)
        total_price = get_user_cart_total(request.user)
        html = render_to_string('cart/_mini_cart.html', {'cart_items': items, 'total_price': total_price}, request=request)
        cart_count = items.count()
        return JsonResponse({'status': 'success', 'message': 'Quantity decreased', 'html': html, 'cart_count': cart_count})

    return redirect('cart:cart_detail')


@login_required
def cart_count(request):
    total_quantity = CartItem.objects.filter(user=request.user).aggregate(total=models.Sum('quantity'))['total'] or 0
    return JsonResponse({'cart_count': total_quantity})

