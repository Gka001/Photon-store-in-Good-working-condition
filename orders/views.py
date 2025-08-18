from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CheckoutForm
from cart.models import CartItem
from .models import Order, OrderItem, InsufficientStock  # <- InsufficientStock used by reserved flow
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import razorpay
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
from django.contrib import messages
from .utils import get_delivery_range
from products.models import Review, Product
from django.db import transaction
from django.urls import reverse
from cart.utils import get_user_cart_total, get_user_cart


@login_required
def checkout(request):
    form = CheckoutForm()
    total_price = get_user_cart_total(request.user)

    latest_order = Order.objects.filter(user=request.user).order_by('-order_date').first()
    delivery_range = get_delivery_range(latest_order) if latest_order else None

    cart_items = get_user_cart(request.user)

    return render(request, 'cart/checkout.html', {
        'form': form,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'cart_total': total_price,
        'delivery_range': delivery_range,
        'cart_items': cart_items,
    })


# ----------------------------
# Original (legacy) endpoints
# ----------------------------

@csrf_exempt
def create_razorpay_order(request):
    """
    Original flow (kept for compatibility).
    Quick availability check, then create a Razorpay order with auto-capture.
    """
    if request.method == "POST":
        cart_items = get_user_cart(request.user)
        for item in cart_items:
            if item.product.available < item.quantity:
                return JsonResponse(
                    {'success': False, 'error': f"Insufficient stock for {item.product.name}"},
                    status=409
                )

        total_amount = int(get_user_cart_total(request.user) * 100)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {"amount": total_amount, "currency": "INR", "payment_capture": "1"}
        razorpay_order = client.order.create(data=order_data)

        return JsonResponse({
            "success": True,
            "razorpay_order_id": razorpay_order['id'],
            "amount": razorpay_order['amount']
        })

    return HttpResponseBadRequest("Invalid request method.")


@csrf_exempt
@transaction.atomic
def razorpay_payment(request):
    """
    Original flow (kept). Verifies signature, creates Order, then reserve->confirm.
    On race, auto-refund.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_items = get_user_cart(request.user)
        total_price = get_user_cart_total(request.user)

        name = data.get('name')
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        pincode = data.get('pincode')
        phone = data.get('phone')
        email = data.get('email')

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

        generated_signature = hmac.new(
            key=bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            msg=bytes(razorpay_order_id + "|" + razorpay_payment_id, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            return JsonResponse({'success': False, 'error': 'Payment verification failed'}, status=400)

        order = Order.objects.create(
            name=name, address=address, city=city, state=state, pincode=pincode,
            phone=phone, email=email, total_price=total_price, status='Pending',
            user=request.user, payment_id=razorpay_payment_id
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product, price=item.product.price, quantity=item.quantity
            )

        try:
            order.reserve_inventory()
            order.confirm_inventory()
        except InsufficientStock as e:
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                client.payment.refund(razorpay_payment_id, {"amount": int(total_price * 100)})
            except Exception:
                pass
            order.mark_as_failed()
            return JsonResponse({'success': False, 'error': str(e)}, status=409)

        if email:
            subject = f"Photon Cure - Order #{order.id} Confirmation"
            message = render_to_string('orders/email/order_confirmation.txt', {
                'order': order,
                'cart_items': cart_items,
                'expected_start': order.expected_delivery_range[0],
                'expected_end': order.expected_delivery_range[1],
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

        request.session['latest_order_id'] = order.id
        CartItem.objects.filter(user=request.user).delete()

        return JsonResponse({'success': True, 'redirect_url': reverse('orders:order_success')})

    return HttpResponseBadRequest("Invalid request method.")


# ----------------------------
# Common pages
# ----------------------------

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

    delivery_ranges = {order.id: get_delivery_range(order) for order in orders}

    reviewed_products = set(
        Review.objects.filter(user=request.user).values_list('product_id', flat=True)
    )

    return render(request, 'orders/order_history.html', {
        'orders': orders,
        'delivery_ranges': delivery_ranges,
        'reviewed_products': reviewed_products,
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
    """
    Uses model helper so reservations (if any) are released for Pending orders.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        if order.status == 'Pending':
            order.mark_as_cancelled()
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


# -----------------------------------------
# Reserved flow (Option B) — AUTO-CAPTURE
# -----------------------------------------

@csrf_exempt
@login_required
@transaction.atomic
def create_razorpay_order_reserved(request):
    """
    Create a local Order + OrderItems and RESERVE inventory BEFORE opening Razorpay.
    If reservation fails, we don't show the payment sheet.
    Then create a Razorpay order with auto-capture (payment_capture=1).
    Expects JSON: { name, address, city, state, pincode, phone, email }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        data = {}

    cart_items = list(get_user_cart(request.user))
    if not cart_items:
        return JsonResponse({"success": False, "error": "Your cart is empty."}, status=400)

    total_price = get_user_cart_total(request.user)

    # Create local order snapshot
    order = Order.objects.create(
        name=data.get('name') or "Guest",
        address=data.get('address') or "",
        city=data.get('city') or "",
        state=data.get('state') or "",
        pincode=data.get('pincode') or "",
        phone=data.get('phone') or "",
        email=data.get('email') or "",
        total_price=total_price,
        status='Pending',
        user=request.user,
    )
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            price=item.product.price,
            quantity=item.quantity
        )

    # Reserve under locks
    try:
        order.reserve_inventory()
    except InsufficientStock as e:
        order.delete()
        return JsonResponse({'success': False, 'error': str(e)}, status=409)

    # With stock reserved, create Razorpay order with AUTO-CAPTURE
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    rzp_order = client.order.create(data={
        "amount": int(total_price * 100),
        "currency": "INR",
        "payment_capture": "1",  # <— auto-capture
        "notes": {"local_order_id": str(order.id)}
    })

    request.session['pending_order_id'] = order.id

    return JsonResponse({
        "success": True,
        "razorpay_order_id": rzp_order['id'],
        "amount": rzp_order['amount'],
        "local_order_id": order.id
    })


@csrf_exempt
@login_required
@transaction.atomic
def razorpay_finalize_reserved(request):
    """
    Finalize after Razorpay 'success':
      - verify signature
      - confirm inventory (allocated->sold)
      - email, clear cart, redirect
    NOTE: We DO NOT capture here (already auto-captured by Razorpay).
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    data = json.loads(request.body.decode() or "{}")
    local_order_id = data.get('local_order_id')
    if not local_order_id:
        return JsonResponse({'success': False, 'error': 'Missing local order id.'}, status=400)

    try:
        order = Order.objects.select_for_update().get(id=local_order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)

    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')

    # Verify signature
    generated_signature = hmac.new(
        key=bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
        msg=bytes(f"{razorpay_order_id}|{razorpay_payment_id}", 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    if generated_signature != razorpay_signature:
        order.release_inventory()
        order.mark_as_failed()
        return JsonResponse({'success': False, 'error': 'Payment verification failed'}, status=400)

    # Persist payment id (already captured by Razorpay)
    order.payment_id = razorpay_payment_id
    order.save(update_fields=['payment_id'])

    # Confirm (allocated -> sold)
    try:
        order.confirm_inventory()
    except InsufficientStock as e:
        # Extremely unlikely; in this case refund and fail
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.payment.refund(razorpay_payment_id, {"amount": int(order.total_price * 100)})
        except Exception:
            pass
        order.mark_as_failed()
        return JsonResponse({'success': False, 'error': str(e)}, status=409)

    # Email confirmation
    if order.email:
        subject = f"Photon Cure - Order #{order.id} Confirmation"
        message = render_to_string('orders/email/order_confirmation.txt', {
            'order': order,
            'cart_items': list(order.items.select_related('product')),
            'expected_start': order.expected_delivery_range[0],
            'expected_end': order.expected_delivery_range[1],
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])

    # Clear the cart now that order is finalized
    CartItem.objects.filter(user=request.user).delete()

    request.session['latest_order_id'] = order.id
    return JsonResponse({'success': True, 'redirect_url': reverse('orders:order_success')})


@csrf_exempt
@login_required
@transaction.atomic
def release_pending_order(request):
    """
    Called when the Razorpay modal is closed or payment fails on client side.
    Releases the reservation if not finalized yet, and marks as failed.
    Expects JSON: { local_order_id }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    try:
        data = json.loads(request.body.decode())
        local_order_id = int(data.get('local_order_id'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Bad payload'}, status=400)

    try:
        order = Order.objects.select_for_update().get(id=local_order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Order not found'}, status=404)

    if order.inventory_reserved and not order.inventory_finalized:
        order.release_inventory()
        if order.status == 'Pending' and not order.payment_id:
            order.mark_as_failed()

    return JsonResponse({'ok': True})
