from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
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
    cart.add(product=product, quantity=quantity, override_quantity=override)

    # ✅ AJAX response fallback check
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Product added to cart',
            'cart_count': len(cart)
        })

    # ✅ Otherwise redirect
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
    html = render_to_string('cart/_mini_cart.html', {'cart':cart}, request=request)
    return JsonResponse({'html': html})

@require_POST
def cart_increase(request, product_id):
    cart= Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.increase_quantity(product)
    return redirect('cart:cart_detail')

@require_POST
def cart_decrease(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.decrease_quantity(product)
    return redirect('cart:cart_detail')