from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import CheckoutForm
from cart.cart import Cart
from .models import Order, OrderItem
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

@login_required
def checkout(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # Create the Order 
            order = Order.objects.create(
                name=cd['name'],
                address=cd['address'],
                phone=cd['phone'],
                total_price=cart.get_total_price(),
                status='Pending'
            )

            # Create OrderItems for each product in the cart
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )

            # ✅ SEND EMAIL NOTIFICATION
            subject = f"Order Confirmation - Photon Cure (Order #{order.id})"
            message = render_to_string('email/order_confirmation.txt', {
                'order': order,
                'cart': cart,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])


            # Clear the cart after order is placed
            cart.clear()
            return redirect('orders:order_success')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'cart': cart,
        'form': form
    })

def order_success(request):
    return render(request, 'order_success.html')

def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'order_history.html', {'orders': orders})