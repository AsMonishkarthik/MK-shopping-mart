from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'status', 'payment_method', 'is_paid', 'total', 'created_at']
    list_filter = ['status', 'payment_method', 'is_paid']
    list_editable = ['status', 'is_paid']
    search_fields = ['user__username', 'full_name', 'email', 'phone']
    inlines = [OrderItemInline]
    readonly_fields = ['subtotal', 'shipping_fee', 'total', 'created_at']