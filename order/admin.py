from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    # Remove 'product' since your OrderItem model doesn't have a 'product' field
    # raw_id_fields = ['product']  # Commented out
    extra = 0
    fields = ['product_name', 'quantity', 'price']
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Changed 'created' to 'created_at' and 'total_amount' matches your model
    list_display = ['id', 'user', 'first_name', 'last_name', 'email', 'status', 'total_amount', 'created_at']
    # Changed 'created' to 'created_at' and 'updated' to 'updated_at'
    list_filter = ['status', 'created_at', 'updated_at']
    list_editable = ['status']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [OrderItemInline]
    # Changed 'created' to 'created_at'
    date_hierarchy = 'created_at'
    # Changed 'created' to 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = ['order_id', 'customer_name', 'full_address']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'total_amount')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'customer_name')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'postal_code', 'full_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'total_price']
    list_filter = ['user']
    search_fields = ['product_name']