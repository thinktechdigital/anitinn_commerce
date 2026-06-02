from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

from .models import UserProfile, Address, Vendor, Category, Product, Review, Cart, CartItem, Order, OrderItem
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, AddressForm, ProductForm, VendorSettingsForm, ReviewForm

# ----------------- Dynamic Template Helper (For standard static pages) -----------------
def make_static_view(template_name, title):
    def view_func(request):
        return render(request, template_name, {"page_title": title})
    return view_func


# ----------------- Auth Views -----------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('pages:marketplace')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            
            # Update user profile role
            role = form.cleaned_data.get('role')
            profile = user.profile
            profile.role = role
            profile.save()
            
            if role == 'VENDOR':
                Vendor.objects.create(user=user, store_name=f"{user.username}'s Store")
                
            login(request, user)
            messages.success(request, f"Welcome to Anitinn, {user.username}!")
            if role == 'VENDOR':
                return redirect('pages:vendor_dashboard')
            return redirect('pages:marketplace')
    else:
        form = UserRegisterForm()
    return render(request, 'pages/registration.html', {'form': form, 'page_title': 'Register'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('pages:marketplace')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                if user.is_staff or user.profile.role == 'ADMIN':
                    return redirect('pages:admin_dashboard')
                elif user.profile.role == 'VENDOR':
                    return redirect('pages:vendor_dashboard')
                return redirect('pages:marketplace')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, 'pages/login.html', {'form': form, 'page_title': 'Login'})


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('pages:marketplace')


# ----------------- Buyer & Marketplace Views -----------------
def marketplace_view(request):
    categories = Category.objects.annotate(product_count=Count('products'))[:6]
    hot_products = Product.objects.filter(status='ACTIVE').order_by('-created_at')[:4]
    new_products = Product.objects.filter(status='ACTIVE').order_by('-created_at')[:8]
    return render(request, 'pages/marketplace.html', {
        'categories': categories,
        'hot_products': hot_products,
        'new_products': new_products,
        'page_title': 'Marketplace'
    })


def catalog_view(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    products = Product.objects.filter(status='ACTIVE')

    # Filtering
    q = request.GET.get('q')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    cat_slugs = request.GET.getlist('category')
    if cat_slugs:
        products = products.filter(category__slug__in=cat_slugs)

    min_p = request.GET.get('min_price')
    max_p = request.GET.get('max_price')
    if min_p:
        products = products.filter(price__gte=min_p)
    if max_p:
        products = products.filter(price__lte=max_p)

    rating = request.GET.get('rating')
    if rating:
        products = products.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        products = products.order_by('-created_at')

    # For display stats
    total_count = products.count()

    return render(request, 'pages/catalog.html', {
        'categories': categories,
        'products': products,
        'total_count': total_count,
        'page_title': 'Product Catalog'
    })


def product_detail_view(request, product_id=None):
    # Support default product if ID is not specified
    if product_id is None:
        product = Product.objects.filter(status='ACTIVE').first()
        if not product:
            return redirect('pages:catalog')
    else:
        product = get_object_or_404(Product, id=product_id)

    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    reviews_count = reviews.count()

    # Related products
    related = Product.objects.filter(status='ACTIVE', category=product.category).exclude(id=product.id)[:4]

    # Handle review submission
    review_form = None
    if request.user.is_authenticated:
        if request.method == 'POST' and 'submit_review' in request.POST:
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                rev = review_form.save(commit=False)
                rev.product = product
                rev.user = request.user
                rev.save()
                messages.success(request, "Your review has been posted!")
                return redirect('pages:product_detail', product_id=product.id)
        else:
            review_form = ReviewForm()

    return render(request, 'pages/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'reviews_count': reviews_count,
        'related': related,
        'review_form': review_form,
        'page_title': 'Product Detail'
    })


@login_required(login_url='pages:login')
def profile_view(request):
    profile = request.user.profile
    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile details updated successfully.")
                return redirect('pages:profile')
        elif 'add_address' in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                addr = address_form.save(commit=False)
                addr.user = request.user
                if addr.is_default:
                    Address.objects.filter(user=request.user).update(is_default=False)
                addr.save()
                messages.success(request, "New address added successfully.")
                return redirect('pages:profile')
    
    profile_form = UserProfileForm(instance=profile)
    address_form = AddressForm()

    return render(request, 'pages/profile.html', {
        'profile': profile,
        'addresses': addresses,
        'profile_form': profile_form,
        'address_form': address_form,
        'page_title': 'Buyer Profile'
    })


# ----------------- Cart & Checkout Views -----------------
@login_required(login_url='pages:login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    subtotal = sum(item.product.price * item.quantity for item in items)
    discount = sum((item.product.compare_at_price - item.product.price) * item.quantity for item in items if item.product.compare_at_price and item.product.compare_at_price > item.product.price)
    total = subtotal # Discount is already accounted for in price (price is active purchase price)
    
    return render(request, 'pages/cart.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'page_title': 'Shopping Cart'
    })


@login_required(login_url='pages:login')
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check inventory
    if product.stock < quantity:
        messages.error(request, f"Sorry, only {product.stock} items left in stock.")
        return redirect('pages:product_detail', product_id=product.id)
        
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect('pages:cart')


@login_required(login_url='pages:login')
def update_cart_item_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'increase':
        if cart_item.product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(request, "Out of stock for additional items.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
        
    return redirect('pages:cart')


@login_required(login_url='pages:login')
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect('pages:catalog')
        
    addresses = Address.objects.filter(user=request.user)
    subtotal = sum(item.product.price * item.quantity for item in items)
    total = subtotal
    
    if request.method == 'POST':
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method', 'Visa')
        
        address = None
        if address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
        # Create Order
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_price=total,
            status='PENDING',
            payment_method=payment_method,
            tracking_number=f"AN-{uuid.uuid4().hex[:8].upper()}",
            estimated_delivery=timezone.now() + timezone.timedelta(days=3)
        )
        
        # Move items to order items and deduct inventory
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save()
            
        # Clear Cart
        cart.items.all().delete()
        
        messages.success(request, "Order placed successfully!")
        return redirect('pages:order_confirmation', order_id=order.id)
        
    address_form = AddressForm()
    return render(request, 'pages/checkout.html', {
        'items': items,
        'addresses': addresses,
        'address_form': address_form,
        'total': total,
        'page_title': 'Checkout'
    })


@login_required(login_url='pages:login')
def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'pages/order_confirmation.html', {
        'order': order,
        'page_title': 'Order Confirmation'
    })


@login_required(login_url='pages:login')
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'pages/order_history.html', {
        'orders': orders,
        'page_title': 'Order History'
    })


@login_required(login_url='pages:login')
def order_tracking_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'pages/order_tracking.html', {
        'order': order,
        'page_title': 'Order Tracking'
    })


# ----------------- Vendor Views -----------------
@login_required(login_url='pages:login')
def vendor_dashboard_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    products = Product.objects.filter(vendor=vendor)
    products_count = products.count()
    
    # Calculate earnings and order counts
    vendor_order_items = OrderItem.objects.filter(product__vendor=vendor)
    total_sales = vendor_order_items.aggregate(Sum('price'))['price__sum'] or 0.00
    total_orders = vendor_order_items.values('order').distinct().count()
    
    recent_orders = Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')[:5]
    
    return render(request, 'pages/vendor_dashboard.html', {
        'vendor': vendor,
        'products_count': products_count,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'page_title': 'Vendor Dashboard'
    })


@login_required(login_url='pages:login')
def vendor_products_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    
    total_products = products.count()
    active_listings = products.filter(status='ACTIVE').count()
    low_stock = products.filter(stock__lt=5).count()
    
    return render(request, 'pages/vendor_products.html', {
        'products': products,
        'total_products': total_products,
        'active_listings': active_listings,
        'low_stock': low_stock,
        'page_title': 'Vendor Products'
    })


@login_required(login_url='pages:login')
def vendor_product_form_view(request, product_id=None):
    vendor = get_object_or_404(Vendor, user=request.user)
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id, vendor=vendor)
        
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            prod = form.save(commit=False)
            prod.vendor = vendor
            prod.save()
            messages.success(request, "Product saved successfully.")
            return redirect('pages:vendor_products')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'pages/vendor_product_form.html', {
        'form': form,
        'product': product,
        'page_title': 'Manage Product'
    })


@login_required(login_url='pages:login')
def vendor_analytics_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    return render(request, 'pages/vendor_analytics.html', {
        'vendor': vendor,
        'page_title': 'Vendor Analytics'
    })


@login_required(login_url='pages:login')
def vendor_orders_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    orders = Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')
    return render(request, 'pages/vendors_order_management.html', {
        'orders': orders,
        'page_title': 'Vendor Orders'
    })


@login_required(login_url='pages:login')
def vendor_settings_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    if request.method == 'POST':
        form = VendorSettingsForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, "Store settings updated successfully.")
            return redirect('pages:vendor_settings')
    else:
        form = VendorSettingsForm(instance=vendor)
        
    return render(request, 'pages/vendor_settings.html', {
        'form': form,
        'vendor': vendor,
        'page_title': 'Vendor Settings'
    })


@login_required(login_url='pages:login')
def vendor_reviews_view(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    reviews = Review.objects.filter(product__vendor=vendor).order_by('-created_at')
    return render(request, 'pages/vendor_reviews.html', {
        'reviews': reviews,
        'page_title': 'Vendor Reviews'
    })


# ----------------- Admin Views -----------------
@login_required(login_url='pages:login')
def admin_dashboard_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
        
    users_count = User.objects.count()
    vendors_count = Vendor.objects.count()
    orders_count = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0.00
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    return render(request, 'pages/admin_dashboard.html', {
        'users_count': users_count,
        'vendors_count': vendors_count,
        'orders_count': orders_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'page_title': 'Admin Dashboard'
    })


@login_required(login_url='pages:login')
def admin_users_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'pages/admin_users.html', {
        'users': users,
        'page_title': 'Admin Users'
    })


@login_required(login_url='pages:login')
def admin_vendors_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
    vendors = Vendor.objects.all().order_by('-created_at')
    return render(request, 'pages/admin_vendors.html', {
        'vendors': vendors,
        'page_title': 'Admin Vendors'
    })


@login_required(login_url='pages:login')
def admin_moderation_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'pages/admin_moderation.html', {
        'products': products,
        'page_title': 'Product Moderation'
    })


@login_required(login_url='pages:login')
def admin_orders_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'pages/admin_orders.html', {
        'orders': orders,
        'page_title': 'Admin Orders'
    })


@login_required(login_url='pages:login')
def admin_analytics_view(request):
    if not request.user.is_staff and request.user.profile.role != 'ADMIN':
        return redirect('pages:marketplace')
    # Simple aggregations for graph bindings
    return render(request, 'pages/admin_analytics.html', {
        'page_title': 'Admin Analytics'
    })
