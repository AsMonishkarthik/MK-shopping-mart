from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Cart, CartItem
from myapp.models import Product


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_detail(request):
    cart = get_or_create_cart(request.user)
    return render(request, 'cart/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity < product.stock:
            item.quantity += 1
            item.save()
            messages.success(request, f'"{product.name}" quantity updated.')
        else:
            messages.warning(request, 'Not enough stock available.')
    else:
        messages.success(request, f'"{product.name}" added to cart!')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'total_items': cart.total_items, 'message': 'Added to cart'})
    return redirect('cart_detail')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart_detail')


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0 and quantity <= item.product.stock:
        item.quantity = quantity
        item.save()
    elif quantity <= 0:
        item.delete()
    return redirect('cart_detail')


@login_required
def clear_cart(request):
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared.')
    return redirect('cart_detail')