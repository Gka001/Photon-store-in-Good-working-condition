from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CheckoutForm
from cart.cart import Cart
from .models import Order, OrderItem
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import razorpay
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
from django.contrib import messages
from .utils import get_delivery_range
from products.models import Review

@login_required
def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            return render(request, 'cart/checkout.html', {
                'cart': cart,
                'form': form,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID
            })
    else:
        form = CheckoutForm()

    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'form': form,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    })

@csrf_exempt
def create_razorpay_order(request):
    if request.method == "POST":
        cart = Cart(request)
        total_amount = int(cart.get_total_price() * 100)  # paise

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {
            "amount": total_amount,
            "currency": "INR",
            "payment_capture": "1"
        }
        razorpay_order = client.order.create(data=order_data)

        return JsonResponse({
            "razorpay_order_id": razorpay_order['id'],
            "amount": razorpay_order['amount']
        })

@csrf_exempt
def razorpay_payment(request):
    cart = Cart(request)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Verify Razorpay Signature
        generated_signature = hmac.new(
            key=bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            msg=bytes(razorpay_order_id + "|" + razorpay_payment_id, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        if generated_signature == razorpay_signature:
            order = Order.objects.create(
                name=name,
                address=address,
                phone=phone,
                email=email,
                total_price=cart.get_total_price(),
                status='Pending',
                user=request.user if request.user.is_authenticated else None,
                payment_id=razorpay_payment_id
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            # Send order confirmation email
            if email:
                subject = f"Photon Cure - Order #{order.id} Confirmation"
                message = render_to_string('orders/email/order_confirmation.txt', {
                    'order': order,
                    'cart': cart,
                    'expected_start': order.expected_delivery_range[0],  # ✅ FIXED
                    'expected_end': order.expected_delivery_range[1],    # ✅ FIXED
                })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            request.session['latest_order_id'] = order.id
            cart.clear()
            return redirect('orders:order_success')

        return redirect('orders:payment_cancel')

def order_success(request):
    order_id = request.session.get('latest_order_id')
    order = None
    expected_start = expected_end = None

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            expected_start, expected_end = order.expected_delivery_range
            del request.session['latest_order_id']
        except Order.DoesNotExist:
            pass

    return render(request, 'orders/order_success.html', {
        'order': order,
        'expected_start': expected_start,
        'expected_end': expected_end,
    })

def payment_cancel(request):
    return render(request, 'orders/payment_cancel.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date').prefetch_related('items__product')

    delivery_ranges = {
        order.id: get_delivery_range(order)
        for order in orders
    }

    # ✅ Get IDs of products already reviewed by the user
    reviewed_products = set(
        Review.objects.filter(user=request.user).values_list('product_id', flat=True)
    )

    return render(request, 'orders/order_history.html', {
        'orders': orders,
        'delivery_ranges': delivery_ranges,
        'reviewed_products': reviewed_products,  # ✅ Send to template
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    expected_start, expected_end = order.expected_delivery_range

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'expected_start': expected_start,
        'expected_end': expected_end,
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        if order.status == 'Pending':
            order.status = 'Cancelled'
            order.save()

            # Send cancellation email to admin
            subject = f"Photon Cure - Order #{order.id} Cancelled"
            message = render_to_string('orders/email/order_cancelled.txt', {
                'order': order,
                'user': request.user,
                'expected_start': None,
                'expected_end': None,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])

            messages.success(request, f"Order #{order_id} has been cancelled.")
        else:
            messages.warning(request, f"Order #{order.id} cannot be cancelled as it is already {order.status}.")
    else:
        messages.error(request, "Invalid request.")

    return redirect('orders:order_history')
