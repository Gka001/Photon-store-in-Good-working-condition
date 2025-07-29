from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Review
from django.db.models import Q, Avg, Count
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Greatest

def product_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    sort = request.GET.get('sort')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()
    categories = Category.objects.all()

    if query:
        products = products.annotate(
            similarity=Greatest(
                TrigramSimilarity('name', query),
                TrigramSimilarity('description', query)
            )
        ).filter(similarity__gt=0.2).order_by('-similarity')

    if category_id and category_id.isdigit():
        products = products.filter(category_id=int(category_id))

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Annotate with average rating and review count
    products = products.annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )

    # Sort options
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    elif sort == 'rating_high_low':
        products = products.order_by('-average_rating')
    elif sort == 'rating_low_high':
        products = products.order_by('average_rating')

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'selected_sort': sort,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.select_related('user').order_by('-created_at')
    average_rating = product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating
    })


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.reviews.filter(user=request.user).exists():
        messages.warning(request, "You have already reviewed this product.")
        return redirect('orders:order_history')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating. Please choose between 1 and 5.")
            return redirect('orders:order_history')

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, "Thank you for your review!")
        return redirect('orders:order_history')

    messages.error(request, "Invalid request method.")
    return redirect('orders:order_history')
