from .models import Cart, CartItem
from .views import _cart_id

def items_counter(request):
    cart_count=0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
                
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
                
            for item in cart_items:
                cart_count += item.quantity
        
        except Cart.DoesNotExist:
            pass
        
        return dict(cart_count=cart_count)
                