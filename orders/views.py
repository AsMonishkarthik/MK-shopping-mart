from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem
from cart.models import Cart
from decimal import Decimal


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.items.count() == 0:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_detail')

    shipping_fee = Decimal('50.00') if cart.total_price < 500 else Decimal('0.00')

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            pincode=request.POST.get('pincode'),
            payment_method=request.POST.get('payment_method', 'cod'),
            notes=request.POST.get('notes', ''),
            subtotal=cart.total_price,
            shipping_fee=shipping_fee,
            total=cart.total_price + shipping_fee,
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.final_price,
                quantity=item.quantity,
            )
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_confirmation', order_id=order.id)

    context = {
        'cart': cart,
        'shipping_fee': shipping_fee,
        'total': cart.total_price + shipping_fee,
        'user': request.user,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Only allow cancellation if order hasn't shipped yet
    cancellable_statuses = ['pending', 'confirmed']

    if order.status not in cancellable_statuses:
        messages.error(request, f'Order #{order.id} cannot be cancelled — it is already {order.get_status_display()}.')
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        # Restore stock for each item
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()

        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} has been cancelled successfully.')
        return redirect('order_list')

    # GET → show confirmation page
    return render(request, 'orders/cancel_confirm.html', {'order': order})