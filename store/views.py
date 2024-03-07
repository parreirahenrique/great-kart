from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib import messages

from .models import Product, Category, ReviewRating, ProductGallery
from .forms import ReviewForm
from cart.models import CartItem
from cart.views import _cart_id
from orders.models import OrderProduct

# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None
    
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('product_name')
                
    else:  
        products = Product.objects.all().filter(is_available=True).order_by('product_name')
        
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()
    
    context = {
        'products': paged_products,
        'product_count': product_count
    }
    
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
    
    try: 
        orderProduct = OrderProduct.objects.filter(user=request.user, product_id=product.id).exists()
        
    except:
        orderProduct = False
    
    reviews = ReviewRating.objects.filter(product_id = product.id, status=True)
    
    product_gallery = ProductGallery.objects.filter(product_id = product.id)
    
    context = {
        'product': product,
        'in_cart': in_cart,
        'orderProduct': orderProduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    
    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        
        if keyword:
            products = Product.objects.order_by('-created_at').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
        
        product_count = products.count()
        
        context = {
            'products': products,
            'product_count': product_count
        }
        
        return render(request, 'store/store.html', context)
    
def submitReview(request, product_id):
    url = request.META.get('HTTP_REFERER')
    
    if request.method == "POST":
        print()
        try:
            review = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            
            return redirect(url)
            
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            
            if form.is_valid():
                review = ReviewRating()
                review.subject = form.cleaned_data['subject']
                review.review = form.cleaned_data['review']
                review.rating = form.cleaned_data['rating']
                review.ip = request.META.get('REMOTE_ADDR')
                review.product_id = product_id
                review.user_id = request.user.id
                review.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                
                return redirect(url)
                