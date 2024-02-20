from django.contrib import admin
from django.db import models
from .models import Product, Variation

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'price', 'stock', 'category', 'modified_at', 'is_available'
    )
    prepopulated_fields = {
        'slug': ('product_name',)
    }
    
class VariationAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'variation_category', 'variation_value', 'is_active', 'created_date'
    )
    list_editable = ('is_active',)
    list_filter = (
        'product', 'variation_category', 'variation_value', 'is_active'
    )

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)