from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from cart.models import Cart, CartItem
from cart.views import _cart_id
from orders.models import Order, OrderProduct

import requests

# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            password = form.cleaned_data["password"]
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                username=username
            )
            user.phone_number = phone_number
            user.save()
            
            # Create User Profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()
            
            # User activation
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),              
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for registering! An activation email was sent to your email address.')
            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
    }

    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        
        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_item_exists = CartItem.objects.filter(cart=cart).exists()

                if cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                        
                    cart_items = CartItem.objects.filter(user=user)
                    id = []
                    existing_variations_list = []
                    
                    for item in cart_items:
                        id.append(item.id)
                        existing_variations = item.variations.all()
                        existing_variations_list.append(list(existing_variations))
                        
                    for variation in product_variation:
                        if variation in existing_variations_list:
                            index = existing_variations_list.index(variation)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                            
                        else:
                            cart_item = CartItem.objects.get(cart=cart)
                            
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            
            auth.login(request, user)
            messages.success(request, "You are now logged in")
            url = request.META.get('HTTP_REFERER')
            
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
                
            except:
                return redirect('dashboard')
            
        else:
            messages.error(request, "Invalid login credentials")
            return redirect('login')
        
    return render(request, 'accounts/login.html')

@login_required(login_url = "login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out")
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations, your account is activated!")
        return redirect('login')
    
    else:
        messages.error(request, "Invalid activation link")
        return redirect('register')
    
@login_required(login_url = "login")
def dashboard(request):
    orders = Order.objects.filter(user_id=request.user.id, is_ordered=True)
    user_profile = UserProfile.objects.get(user=request.user)
    
    context = {
        'orders_count': orders.count(),
        'user_profile': user_profile,
    }
    
    return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            
            # Reset password email
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),              
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, "An email has been sent to your email address")
            return redirect('login')
        
        else:
            messages.error(request, "Account does not exist")
            return redirect('forgotPassword')
        
    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password")
        return redirect('resetPassword')
    
    else:
        messages.error(request, "This link has been expired")
        return redirect('login')
    
def resetPassword(request):
    if request.method == "POST":
       password = request.POST["password"]
       confirm_password = request.POST["confirm_password"]
       
       if password == confirm_password:
           uid = request.session.get('uid')
           user = Account.objects.get(pk=uid)
           user.set_password(password)
           user.save()
           messages.success(request, "Password reset")
           return redirect('login')
       
       else:
           messages.error(request, "Password does not match")
           return redirect('resetPassword')
    
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url = "login")    
def myOrders(request):
    orders = Order.objects.filter(user_id=request.user.id, is_ordered=True).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url = "login")
def editProfile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            messages.success(request, 'Your profile has been updated.')
            return redirect('editProfile')
        
    else:
        print('here bitch')
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        print(user_form)
        print(profile_form)
        context = {
            'user_profile': user_profile,
            'user_form': user_form,
            'profile_form': profile_form,
        }
        
        return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url = "login")
def changePassword(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        repeat_new_password = request.POST["repeat_new_password"]
        
        user = Account.objects.get(username__exact=request.user.username)
        
        if new_password == repeat_new_password:
            success = user.check_password(current_password)
            
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully')
            
            else:
                messages.error(request, 'Please enter the valid current password')
                
            return redirect('changePassword')
        
        else:
            messages.error(request, 'New passwords do not match')
            
            return redirect('changePassword')
        
    else:
        return render(request, 'accounts/change_password.html')
    
@login_required(login_url = "login")
def orderDetail(request, order_number):
    order_products = OrderProduct.objects.filter(order__order_number=order_number)
    order = Order.objects.get(order_number=order_number)
    
    total = 0
    
    for product in order_products:
        total += product.quantity * product.product.price
    
    context = {
        'order': order,
        'order_products': order_products,
        'total': total,
    }
    
    return render(request, 'accounts/order_detail.html', context)