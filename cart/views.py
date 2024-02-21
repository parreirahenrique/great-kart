from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from .models import Cart, CartItem

# Create your views here.


def cart(request, total=0, quantity=0, tax=0, grand_total=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity

        tax = .02 * total
        grand_total = tax + total

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'tax': round(tax, 2),
        'grand_total': grand_total,
        'cart_items': cart_items
    }

    return render(request, 'store/cart.html', context)


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
                
            except:
                pass
        
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    cart.save()

    cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    
    if cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        id = []
        existing_variations_list = []
        
        for item in cart_items:
            id.append(item.id)
            existing_variations = item.variations.all()
            existing_variations_list.append(list(existing_variations))
        
        if product_variation in existing_variations_list:
            index = existing_variations_list.index(product_variation)
            item = CartItem.objects.get(product=product, id=id[index])
            item.quantity += 1
            item.save()
        
        else:
            item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)
                
            item.save()
    
    else: 
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
        )
        
        if len(product_variation) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        
        cart_item.save()
        
    return redirect('cart')


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def delete_cart(request, product_id, cart_item_id):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        product = get_object_or_404(Product, id=product_id)
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except:
        pass
    return redirect('cart')