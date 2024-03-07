from django.shortcuts import render
from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_at')
    
    for product in products:
        reviews = ReviewRating.objects.filter(product_id = product.id, status=True)
    
    context = {
        'reviews': reviews,
        'products': products,
    }
    
    return render(request, 'home.html', context)