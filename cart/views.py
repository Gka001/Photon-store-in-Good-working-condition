from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from products.models import Product
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    override = request.POST.get('override') == 'true'

    # Calculate total quantity that would result
    existing_quantity = cart.get_quantity(product)
    new_quantity = quantity if override else existing_quantity + quantity

    # Stock validation
    if new_quantity > product.stock:
        message = f"Only {product.stock} items of '{product.name}' in stock."

        # AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': message,
                'cart_count': len(cart)
            })

        # Non-AJAX
        messages.error(request, message)
        return redirect('products:product_detail', slug=product.slug)

    cart.add(product=product, quantity=quantity, override_quantity=override)

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Product added to cart',
            'cart_count': len(cart)
        })

    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


def cart_mini_preview(request):
    cart = Cart(request)
    html = render_to_string('cart/_mini_cart.html', {'cart': cart}, request=request)
    return JsonResponse({'html': html})


@require_POST
def cart_increase(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    current_quantity = cart.get_quantity(product)
    if current_quantity + 1 > product.stock:
        messages.error(request, f"Cannot increase. Only {product.stock} in stock.")
    else:
        cart.increase_quantity(product)

    return redirect('cart:cart_detail')


@require_POST
def cart_decrease(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.decrease_quantity(product)
    return redirect('cart:cart_detail')
