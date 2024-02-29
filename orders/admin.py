from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Payment, Order, OrderProduct

# Register your models here.
admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(OrderProduct)