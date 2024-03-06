from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Payment, Order, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ['payment', 'user', 'product', 'quantity', 'product_price', 'ordered']
    
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'full_name', 'phone_number', 'email', 'city', 'order_total', 'status', 'is_ordered'
    ]
    list_filter = [
        'status', 'is_ordered'
    ]
    search_fields = [
        'order_number', 'first_name', 'last_name', 'phone_number', 'email'
    ]
    list_per_page = 20
    inlines = [OrderProductInline]
    
# Register your models here.
admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)