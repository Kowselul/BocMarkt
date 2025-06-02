from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from . forms import CreateUserForm, LoginForm, ProductForm, EmailChangeForm
from .models import Product, Category, FavoriteProduct, UserProfile, CartItem, ProductImage, OrderItem, Order, Wallet, Transaction, Withdrawal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import auth, User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django import forms
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from .utils import process_image
from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from django.contrib.messages import get_messages



def homepage(request):
    # Renders the homepage of the application.
    return render(request, 'index.html')


def register(request):
    # Handles user registration.
    # If the user is already authenticated, redirect to the dashboard.
    # Ensures passowrd doesn't contain personal information.
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password1 = form.cleaned_data.get('password1')
            password2 = form.cleaned_data.get('password2')
            email = form.cleaned_data.get('email')
            last_name = form.cleaned_data.get('last_name')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username already exists.')
                return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            if password1.isdigit() or password1.isalpha():
                messages.error(request, 'Password must contain both letters and numbers.')
                return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            if last_name and last_name.lower() in password1.lower():
                messages.error(request, 'Password cannot contain your last name.')
                return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            if email:
                email_name = email.split('@')[0]
                if email_name.lower() in password1.lower():
                    messages.error(request, 'Password cannot contain part of your email address.')
                    return render(request, 'register.html', {'form': form, 'is_auth_page': True})

            user = form.save()
            user.userprofile.date_of_birth = form.cleaned_data.get('date_of_birth')
            user.userprofile.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = CreateUserForm()
    
    return render(request, 'register.html', {'form': form, 'is_auth_page': True})


def login_view(request):
    # Handles user login:
    # Validates username existence
    # Verifies password
    # Manages the login session
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            if not User.objects.filter(username=username).exists():
                messages.error(request, 'This username does not exist.')
                return render(request, 'login.html', {'form': form, 'is_auth_page': True})
            
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'The password is wrong, try again.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form, 'is_auth_page': True})


def logout_view(request):
    # Handles user logout:
    # Clears the session and redirects to the homepage.
    auth.logout(request)
    return redirect('/')


@login_required(login_url='login')
def account_settings(request):
    # Handles account settings:
    # Allows users to change their username, password, email, and profile information.
    # Validates the new username and password.
    action = request.GET.get('action', 'info')
    password_form = PasswordChangeForm(request.user)
    email_form = EmailChangeForm()
    
    if request.method == 'POST':
        if action == 'username':
            if request.user.userprofile.username_changes >= 1:
                messages.error(request, 'You have already used your username change.')
            else:
                new_username = request.POST.get('username')
                if new_username:
                    if new_username == request.user.username:
                        messages.error(request, 'The new username must be different from your current username.')
                    elif len(new_username) < 4:
                        messages.error(request, 'Username must be at least 4 characters long.')
                    elif new_username[0].isdigit():
                        messages.error(request, 'Username cannot start with a number.')
                    elif User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                        messages.error(request, 'This username is already taken.')
                    else:
                        request.user.username = new_username
                        request.user.userprofile.username_changes += 1
                        request.user.userprofile.save()
                        request.user.save()
                        messages.success(request, 'Username successfully updated!')
            
        elif action == 'info':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            if date_of_birth := request.POST.get('date_of_birth'):
                try:
                    dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                    max_age = date.today() - relativedelta(years=100)
                    
                    if dob < max_age:
                        messages.error(request, 'Date of birth cannot be more than 100 years ago.')
                    elif dob > date.today():
                        messages.error(request, 'Date of birth cannot be in the future.')
                    else:
                        request.user.userprofile.date_of_birth = dob
                        request.user.userprofile.save()
                        request.user.save()
                        messages.success(request, 'Profile information updated successfully!')
                except ValueError:
                    messages.error(request, 'Invalid date format')
            else:
                request.user.save()
                messages.success(request, 'Profile information updated successfully!')

        elif action == 'password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error[0])

        elif action == 'email':
            email_form = EmailChangeForm(request.POST)
            if email_form.is_valid():
                new_email = email_form.cleaned_data['email']
                if new_email == request.user.email:
                    messages.error(request, 'The new email must be different from your current email.')
                else:
                    request.user.email = new_email
                    request.user.save()
                    messages.success(request, 'Your email was successfully updated!')
            else:
                for error in email_form.errors.values():
                    messages.error(request, error[0])

    context = {
        'password_form': password_form,
        'email_form': email_form,
        'is_auth_page': False,
        'active_tab': action,
        'today': date.today(),
        'min_date': date.today() - relativedelta(years=100)
    }
    
    return render(request, 'account_settings.html', context)


@login_required
def dashboard(request):
    # Handles the dashboard view:
    # Displays active and sold listings for the logged-in user.
    # Allows filtering by category.
    # Displays the number of active and sold listings.
    category_id = request.GET.get('category')
    active_listings = Product.objects.filter(user=request.user, is_sold=False)
    sold_listings = Product.objects.filter(user=request.user, is_sold=True)
    
    if category_id:
        active_listings = active_listings.filter(category_id=category_id)
        sold_listings = sold_listings.filter(category_id=category_id)
    
    active_listings = active_listings.order_by('-created_at')
    sold_listings = sold_listings.order_by('-sold_date')
    
    context = {
        'active_listings': active_listings,
        'sold_listings': sold_listings,
        'categories': Category.objects.all(),
        'is_auth_page': False
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def add_product(request):
    # Handles adding a new product:
    # Validates the product form and ensures at least one image is uploaded.
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            images = request.FILES.getlist('images')
            if not images:
                messages.error(request, 'At least one product image is required.')
                return render(request, 'add_product.html', {'form': form})
            
            if len(images) > 5:
                messages.error(request, 'You can upload maximum 5 images per product.')
                return render(request, 'add_product.html', {'form': form})

            with transaction.atomic():
                product = form.save(commit=False)
                product.user = request.user
                product.save()

                for index, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=(index == 0),
                        order=index
                    )

                messages.success(request, 'Product added successfully!')
                return HttpResponseRedirect(reverse('dashboard'))
    else:
        form = ProductForm()
    
    return render(request, 'add_product.html', {'form': form})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the form data
                    product = form.save()
                    
                    # Get new images if any were uploaded
                    images = request.FILES.getlist('images')
                    current_images_count = product.images.count()
                    
                    # Only validate new images if they were uploaded
                    if images:
                        if current_images_count + len(images) > 5:
                            messages.error(request, 'Maximum 5 images allowed per product.')
                        else:
                            for index, image in enumerate(images):
                                ProductImage.objects.create(
                                    product=product,
                                    image=image,
                                    is_primary=(current_images_count == 0 and index == 0),
                                    order=current_images_count + index
                                )
                    
                    messages.success(request, 'Product updated successfully!')
                    return HttpResponseRedirect(reverse('dashboard'))
                    
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'edit_product.html', {
        'form': form,
        'product': product
    })

@login_required
def delete_product_image(request, image_id):
    # Handles deleting a product image:
    # Ensures the image belongs to the logged-in user.
    # If the deleted image was primary, set the first image as primary.
    # Returns a JSON response indicating success or failure.
    if request.method == 'POST':
        image = get_object_or_404(ProductImage, id=image_id, product__user=request.user)
        is_primary = image.is_primary
        image.delete()
        
        if is_primary:
            first_image = image.product.images.first()
            if first_image:
                first_image.is_primary = True
                first_image.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required(login_url='login')
def delete_product(request, product_id):
    # Handles deleting a product:
    # Ensures the product belongs to the logged-in user.
    product = get_object_or_404(Product, id=product_id)
    if product.user == request.user:
        product.delete()
    return redirect('dashboard')

@login_required
def toggle_favorite(request, product_id):
    # Handles toggling a product as favorite:
    # Checks if the product is already favorited by the user.
    # If it is, remove it from favorites. Otherwise, add it.
    # Returns a JSON response indicating success or failure.
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        favorite = FavoriteProduct.objects.filter(user=request.user, product=product)
        
        if favorite.exists():
            favorite.delete()
            is_favorite = False
        else:
            FavoriteProduct.objects.create(user=request.user, product=product)
            is_favorite = True
        
        new_count = FavoriteProduct.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'count': new_count
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required(login_url='login')
def marketplace(request):
    # Handles the marketplace view:
    # Displays all products with filtering and sorting options.
    # Allows filtering by category, price range, and sorting by various criteria.
    products_list = Product.objects.all()
    
    category_id = request.GET.get('category')
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort_by')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if category_id:
        try:
            selected_category = int(category_id)
            products_list = products_list.filter(category_id=selected_category)
        except (ValueError, TypeError):
            selected_category = None
    else:
        selected_category = None

    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if sort_by:
        if sort_by == 'price_low':
            products_list = products_list.order_by('price')
        elif sort_by == 'price_high':
            products_list = products_list.order_by('-price')
        elif sort_by == 'date_new':
            products_list = products_list.order_by('-created_at')
        elif sort_by == 'date_old':
            products_list = products_list.order_by('created_at')
    else:
        products_list = products_list.order_by('-created_at')

    paginator = Paginator(products_list, 20)
    products = paginator.get_page(page_number)

    for product in products:
        product.is_favorited = FavoriteProduct.objects.filter(
            user=request.user,
            product=product
        ).exists()

    return render(request, 'marketplace.html', {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': selected_category,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'is_auth_page': False
    })

@login_required(login_url='login')
def product_detail(request, product_id):
    # Handles the product detail view:
    # Displays product information, images, and allows users to favorite the product.
    # Checks if the product is already favorited by the user.
    product = get_object_or_404(Product, id=product_id)
    is_owner = product.user == request.user
    
    if request.user.is_authenticated:
        product.is_favorited = product.favorited_by.filter(id=request.user.id).exists()
        product.in_cart = CartItem.objects.filter(user=request.user, product=product).exists()
    else:
        product.is_favorited = False
        product.in_cart = False
    
    is_favorited = FavoriteProduct.objects.filter(user=request.user, product=product).exists()
    
    context = {
        'product': product,
        'is_favorited': is_favorited,
        'is_owner': is_owner,
        'is_auth_page': False
    }
    return render(request, 'product_detail.html', context)

@login_required(login_url='login')
def favorites(request):
    # Handles the favorites view:
    # Displays all products favorited by the logged-in user.
    # Allows filtering by category and sorting by various criteria.
    # Displays the number of favorited products.
    category_id = request.GET.get('category')
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort_by')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    products_list = Product.objects.filter(product_favorites__user=request.user)
    
    if category_id:
        try:
            selected_category = int(category_id)
            products_list = products_list.filter(category_id=selected_category)
        except (ValueError, TypeError):
            selected_category = None
    else:
        selected_category = None

    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if sort_by:
        if sort_by == 'price_low':
            products_list = products_list.order_by('price')
        elif sort_by == 'price_high':
            products_list = products_list.order_by('-price')
        elif sort_by == 'date_new':
            products_list = products_list.order_by('-created_at')
        elif sort_by == 'date_old':
            products_list = products_list.order_by('created_at')
    else:
        products_list = products_list.order_by('-created_at')

    paginator = Paginator(products_list, 20)
    products = paginator.get_page(page_number)

    return render(request, 'favorites.html', {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': selected_category,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'is_auth_page': False
    })

def get_favorites_count(request):
    # Returns the count of favorited products for the logged-in user.
    # If the user is not authenticated, returns 0.
    if request.user.is_authenticated:
        count = FavoriteProduct.objects.filter(user=request.user).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

@login_required
def user_profile(request):
    # Handles the user profile view:
    # Displays the user's profile information and allows updating the profile picture and bio.
    profile = request.user.userprofile
    
    if request.method == 'POST':
        if 'form_type' in request.POST:
            if request.POST['form_type'] == 'profile_picture':
                if 'profile_picture' in request.FILES:
                    if profile.profile_picture:
                        profile.profile_picture.delete()
                    profile.profile_picture = request.FILES['profile_picture']
                    profile.save()
            elif request.POST['form_type'] == 'bio':
                new_bio = request.POST.get('bio', '')[:500]
                profile.bio = new_bio
                profile.save()
        else:
            if 'bio' in request.POST:
                new_bio = request.POST.get('bio', '')[:500]
                profile.bio = new_bio
                profile.save()

    user_listings = Product.objects.filter(
        user=request.user,
        is_sold=False
    ).order_by('-created_at')
    
    paginator = Paginator(user_listings, 12)
    page_number = request.GET.get('page', 1)
    listings = paginator.get_page(page_number)

    return render(request, 'user_profile.html', {
        'profile': profile,
        'listings': listings,
        'is_auth_page': False
    })

def view_user_profile(request, user_id):
    # Handles viewing another user's profile:
    # Displays the user's profile information and their active listings.
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile
    
    user_listings = Product.objects.filter(
        user=user,
        is_sold=False
    ).order_by('-created_at')
    
    paginator = Paginator(user_listings, 12)
    page_number = request.GET.get('page', 1)
    listings = paginator.get_page(page_number)

    return render(request, 'user_profile.html', {
        'viewed_user': user,
        'profile': profile,
        'listings': listings,
        'is_auth_page': False
    })

@login_required
def view_cart(request):
    # Handles the cart view:
    # Displays all products in the user's cart.
    # Calculates the total price of the items in the cart.
    # Allows removing items from the cart.
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total_price = sum(item.product.price for item in cart_items)
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'is_auth_page': False
    })

@login_required
def toggle_cart(request, product_id):
    # Handles toggling a product in the cart:
    # Checks if the product is already in the cart.
    # If it is, remove it from the cart. Otherwise, add it.
    # Returns a JSON response indicating success or failure.
    product = get_object_or_404(Product, id=product_id)
    
    if product.user == request.user:
        return JsonResponse({
            'success': False,
            'message': 'You cannot purchase your own products'
        }, status=400)
    
    if product.is_sold:
        return JsonResponse({
            'success': False,
            'message': 'This product is no longer available'
        }, status=400)

    cart_item = CartItem.objects.filter(user=request.user, product=product)
    
    if cart_item.exists():
        cart_item.delete()
        in_cart = False
    else:
        CartItem.objects.create(user=request.user, product=product)
        in_cart = True
    
    return JsonResponse({
        'success': True,
        'in_cart': in_cart,
        'cart_count': CartItem.objects.filter(user=request.user).count()
    })

@login_required
def cart_count(request):
    # Returns the count of items in the user's cart.
    # If the user is not authenticated, returns 0.
    count = CartItem.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})

def get_cart_count(request):
    # Returns the count of items in the user's cart.
    # If the user is not authenticated, returns 0.
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})


@login_required
def checkout(request):
    # Handles the checkout view:
    # Displays all products in the user's cart.
    cart_items = CartItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__images')
    total_price = sum(item.product.price for item in cart_items)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'is_auth_page': False,
        'wallet': wallet
    })


@login_required
def submit_order(request):
    # Handles the order submission:
    # Validates the payment method and checks for sufficient wallet balance.
    try:
        with transaction.atomic():
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            if not cart_items.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Your cart is empty'
                }, status=400)

            total_amount = sum(item.product.price for item in cart_items)
            payment_method = request.POST.get('payment_method')

            if payment_method == 'wallet':
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                if wallet.balance < total_amount:
                    return JsonResponse({
                        'success': False,
                        'message': 'Insufficient wallet balance'
                    }, status=400)
                
                wallet.balance -= total_amount
                wallet.save()

                Transaction.objects.create(
                    wallet=wallet,
                    amount=-total_amount,
                    type='PURCHASE',
                    description=f"Purchase of {len(cart_items)} items"
                )

            order = Order.objects.create(
                user=request.user,
                full_name=request.POST.get('full_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                city=request.POST.get('city'),
                county=request.POST.get('county'),
                country=request.POST.get('country'),
                zip_code=request.POST.get('zip_code'),
                payment_method=payment_method,
                total_amount=total_amount,
                status='completed'
            )

            for cart_item in cart_items:
                product = cart_item.product
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price
                )
                
                if not product.is_sold:
                    seller_wallet, _ = Wallet.objects.get_or_create(user=product.user)
                    seller_wallet.balance += product.price
                    seller_wallet.save()

                    Transaction.objects.create(
                        wallet=seller_wallet,
                        amount=product.price,
                        type='SALE',
                        product=product,
                        description=f"Sale of {product.title}"
                    )

                    product.is_sold = True
                    product.sold_date = timezone.now()
                    product.save()

            cart_items.delete()

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('order_success', kwargs={'order_id': order.id})
            })

    except Exception as e:
        print(f"Error in submit_order: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def order_success(request, order_id):
    # Handles the order success view:
    # Displays the order details after successful payment.
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {
        'order': order,
        'is_auth_page': False
    })

@login_required
def cleanup_sold_items(request):
    # Handles the cleanup of sold items:
    # Removes sold products from favorites and carts.
    try:
        sold_products = Product.objects.filter(is_sold=True)

        FavoriteProduct.objects.filter(product__in=sold_products).delete()
        
        CartItem.objects.filter(product__in=sold_products).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def my_orders(request):
    # Handles the user's orders view:
    # Displays all orders made by the logged-in user.
    orders_list = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders_list, 4)
    
    page_number = request.GET.get('page', 1)
    orders = paginator.get_page(page_number)
    
    return render(request, 'my_orders.html', {
        'orders': orders,
        'is_auth_page': False
    })

@login_required
def withdraw_funds(request):
    # Handles the withdrawal of funds from the user's wallet:
    # Validates the withdrawal amount and bank account information.
    if request.method == 'POST':
        try:
            wallet = request.user.wallet
            amount = Decimal(request.POST.get('amount'))
            
            if amount <= wallet.balance:
                withdrawal = Withdrawal.objects.create(
                    wallet=wallet,
                    amount=amount,
                    bank_account=request.POST.get('bank_account'),
                    description=request.POST.get('description'),
                    status='COMPLETED'
                )
                
                wallet.balance -= amount
                wallet.save()
                
                Transaction.objects.create(
                    wallet=wallet,
                    amount=-amount,
                    type='WITHDRAWAL',
                    description=f"Withdrawal to bank account {withdrawal.bank_account}"
                )
                
                messages.success(request, 'Withdrawal completed successfully!')
            else:
                messages.error(request, 'Insufficient funds!')
                
        except Exception as e:
            messages.error(request, f'Error processing withdrawal: {str(e)}')
    
    return redirect('wallet')

@login_required
def wallet_view(request):
    # Handles the wallet view:
    # Displays the user's wallet balance and transaction history.
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions_list = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    paginator = Paginator(transactions_list, 8) 
    page_number = request.GET.get('page', 1)
    transactions = paginator.get_page(page_number)
    
    withdrawals = Withdrawal.objects.filter(wallet=wallet).order_by('-created_at')
    
    return render(request, 'wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'withdrawals': withdrawals,
        'is_auth_page': False
    })


@login_required
def complete_order(request, order_id):
    # Handles the order completion process:
    # Updates the order status and marks products as sold.
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        order.status = 'completed'
        order.save()
        
        for item in order.items.all():
            product = item.product
            if not product.is_sold:
                product.mark_as_sold()
                
                CartItem.objects.filter(product=product).delete()
                FavoriteProduct.objects.filter(product=product).delete()
        
        messages.success(request, 'Order completed successfully!')
        return redirect('my_orders')
    
    return render(request, 'confirm_order_completion.html', {
        'order': order,
        'is_auth_page': False
    })


@login_required
def add_funds(request):
    # Handles adding funds to the user's wallet:
    # Validates the payment method and amount.
    if request.method == 'POST':
        try:
            wallet = request.user.wallet
            amount = Decimal(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')
            
            wallet.balance += amount
            wallet.save()
            
            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type='DEPOSIT',
                description=f"Funds added via {payment_method}"
            )
            
            messages.success(request, f'Successfully added ${amount} to your wallet')
        except Exception as e:
            messages.error(request, f'Error adding funds: {str(e)}')
    
    return redirect('wallet')


def custom_404(request, exception):
    # Custom 404 error handler:
    # Displays a custom 404 error page when a page is not found.
    return render(request, '404.html', status=404)