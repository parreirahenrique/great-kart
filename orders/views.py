from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from cart.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, OrderProduct, Payment

import datetime
import json

# Create your views here.
def placeOrder(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    
    if cart_items.count() <= 0:
        return redirect('store')
    
    for item in cart_items:
        total = (item.quantity * item.product.price)
        quantity += item.quantity
    
    tax = .02 * total
    grand_total = tax + total
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.email = form.cleaned_data['email']
            data.phone_number = form.cleaned_data['phone_number']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.country = form.cleaned_data['country']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'tax': tax,
                'total': total,
                'grand_total': grand_total
            }
            
            return render(request, 'orders/payments.html', context)
        
    else:
        return redirect('checkout')
    
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()
    
    # Move the Cart Items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)
    
    for item in cart_items:
        orderProduct = OrderProduct()
        orderProduct.order_id = order.id
        orderProduct.payment = payment
        orderProduct.user_id = request.user.id
        orderProduct.product_id = item.product_id
        orderProduct.quantity = item.quantity
        orderProduct.product_price = item.product.price
        orderProduct.ordered = True
        orderProduct.save()
        
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderProduct = OrderProduct.objects.get(id=orderProduct.id)
        orderProduct.variation.set(product_variation)
        orderProduct.save()
        
        # Reduce the wuantity of the said products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
        
    # Clear cart
    CartItem.objects.filter(user=request.user).delete()
    
    # Send email for the customer
    mail_subject = "Thank you for your order!"
    message = render_to_string('orders/order_received_email.html', {
        'user': request.user,
        'order': order,
    })
    
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()
    
    # Send Order Number and transaction ID back to sendData method via JSON Response 
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    
    return JsonResponse(data)

def orderComplete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')
    
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=payment_id)
        
        total = 0
        
        for product in ordered_products:
            total += product.quantity * product.product.price
            
        tax = total * 0.02
        grand_total = tax + total
        
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
        }
    
        return render(request, 'orders/order_complete.html', context)
    
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home') 