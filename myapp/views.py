from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg
from .models import Product, Category, Review
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse


def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    categories = Category.objects.all()[:6]
    new_arrivals = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'myapp/home.html', context)


def product_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    category_slug = request.GET.get('category')
    query = request.GET.get('q')
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    else:
        category = None

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_low': 'price',
        'price_high': '-price',
        'name': 'name',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'query': query,
        'sort': sort,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    related = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]

    user_reviewed = False
    if request.user.is_authenticated:
        user_reviewed = Review.objects.filter(product=product, user=request.user).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'related': related,
        'user_reviewed': user_reviewed,
    }
    return render(request, 'store/product_detail.html', context)


@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        Review.objects.update_or_create(
            product=product, user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, 'Review submitted successfully!')
    return __import__('django.shortcuts', fromlist=['redirect']).redirect('product_detail', slug=slug)