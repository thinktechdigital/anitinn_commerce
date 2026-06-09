from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count, F
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
import uuid
import csv
from .models import Category

from .models import (
    UserProfile, Address, Vendor, Category, Product, Review, Cart, CartItem,
    Order, OrderItem, Wishlist, Payment, Shipment, Coupon, Notification,
    SupportTicket, ReturnRequest, VendorPayout, ActivityLog, TrackingEvent, Inventory
)
from .forms import (
    UserRegisterForm, UserLoginForm, UserProfileForm, AddressForm, ProductForm,
    VendorSettingsForm, ReviewForm, SupportTicketForm, CouponForm,
    ReturnRequestForm
)


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or getattr(user.profile, 'role', None) == 'ADMIN')


def require_vendor(request):
    return get_object_or_404(Vendor, user=request.user)


def log_activity(user, action, message, object_type='', object_id=''):
    role = getattr(getattr(user, 'profile', None), 'role', '') if user and user.is_authenticated else ''
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        actor_role=role,
        object_type=object_type,
        object_id=str(object_id) if object_id else '',
        message=message,
    )


def order_vendor_subtotal(order, vendor):
    return sum(
        item.price * item.quantity
        for item in order.items.all()
        if item.product and item.product.vendor_id == vendor.id
    )


def create_mock_tracking_event(order, status, actor_label):
    shipment = getattr(order, 'shipment', None)
    if not shipment:
        shipment = Shipment.objects.create(
            order=order,
            tracking_number=order.tracking_number or f"AN-{uuid.uuid4().hex[:8].upper()}",
        )
    descriptions = {
        'PENDING': 'Order is queued for fulfillment.',
        'SHIPPED': 'Package is in transit through the local mock courier network.',
        'DELIVERED': 'Package has been marked as delivered.',
        'CANCELLED': 'Shipment was cancelled before delivery.',
    }
    locations = {
        'PENDING': 'Accra Fulfillment Desk',
        'SHIPPED': 'Accra Distribution Hub',
        'DELIVERED': order.address.city if order.address else 'Customer Destination',
        'CANCELLED': 'Anitinn Operations',
    }
    TrackingEvent.objects.create(
        shipment=shipment,
        location=locations.get(status, 'Anitinn Logistics'),
        description=f"{descriptions.get(status, 'Shipment status updated.')} Updated by {actor_label}.",
    )
    return shipment


def make_mock_pdf(title, rows):
    def pdf_escape(value):
        return str(value).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    lines = [title, "Generated locally by Anitinn mock report service.", ""]
    lines.extend(" | ".join(pdf_escape(cell) for cell in row) for row in rows[:40])
    text_commands = ["BT", "/F1 10 Tf", "50 780 Td"]
    for index, line in enumerate(lines):
        if index:
            text_commands.append("0 -14 Td")
        text_commands.append(f"({pdf_escape(line[:110])}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1", errors="ignore")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(pdf)


def apply_coupon_to_total(request, subtotal):
    coupon_code = request.session.get('coupon_code')
    if not coupon_code:
        return None, Decimal('0.00'), subtotal

    coupon = Coupon.objects.filter(code=coupon_code, active=True).first()
    now = timezone.now()
    if (
        not coupon
        or (coupon.starts_at and coupon.starts_at > now)
        or (coupon.expires_at and coupon.expires_at < now)
        or (coupon.usage_limit and coupon.used_count >= coupon.usage_limit)
        or subtotal < coupon.minimum_order_amount
    ):
        request.session.pop('coupon_code', None)
        return None, Decimal('0.00'), subtotal

    if coupon.discount_type == Coupon.PERCENT:
        discount = subtotal * (coupon.value / Decimal('100.00'))
    else:
        discount = coupon.value
    discount = min(discount.quantize(Decimal('0.01')), subtotal)
    return coupon, discount, subtotal - discount

# ----------------- Dynamic Template Helper (For standard static pages) -----------------
def make_static_view(template_name, title):
    def view_func(request):
        return render(request, template_name, {"page_title": title})
    return view_func


# ----------------- Auth Views -----------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('pages:catalog')
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
            log_activity(user, 'USER_REGISTERED', f"{user.username} registered as {role}.", 'User', user.id)
                
            login(request, user)
            messages.success(request, f"Welcome to Anitinn, {user.username}!")
            if role == 'VENDOR':
                return redirect('pages:vendor_dashboard')
            return redirect('pages:catalog')
    else:
        form = UserRegisterForm()
    return render(request, 'pages/registration.html', {'form': form, 'page_title': 'Register'})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.profile.role == 'ADMIN':
            return redirect('pages:admin_dashboard')
        if request.user.profile.role == 'VENDOR':
            return redirect('pages:vendor_dashboard')
        return redirect('pages:catalog')
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
                return redirect('pages:catalog')
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
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__status='ACTIVE', products__vendor__status='ACTIVE'))
    )[:6]
    hot_products = Product.objects.filter(status='ACTIVE', vendor__status='ACTIVE', stock__gt=0).select_related('vendor', 'category').order_by('-updated_at', '-created_at')[:4]
    new_products = Product.objects.filter(status='ACTIVE', vendor__status='ACTIVE', stock__gt=0).select_related('vendor', 'category').order_by('-created_at')[:8]
    return render(request, 'pages/marketplace.html', {
        'categories': categories,
        'hot_products': hot_products,
        'new_products': new_products,
        'page_title': 'Marketplace'
    })


def catalog_view(request):
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__status='ACTIVE', products__vendor__status='ACTIVE'))
    ).order_by('name')
    products = (
        Product.objects
        .filter(status='ACTIVE', vendor__status='ACTIVE')
        .select_related('vendor', 'category')
        .annotate(avg_rating=Avg('reviews__rating'), reviews_count=Count('reviews'))
    )

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
        try:
            products = products.filter(price__gte=Decimal(min_p))
        except (InvalidOperation, TypeError):
            messages.error(request, "Enter a valid minimum price.")
    if max_p:
        try:
            products = products.filter(price__lte=Decimal(max_p))
        except (InvalidOperation, TypeError):
            messages.error(request, "Enter a valid maximum price.")

    rating = request.GET.get('rating')
    if rating:
        products = products.filter(avg_rating__gte=rating)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-avg_rating', '-updated_at')
    elif sort_by == 'stock':
        products = products.order_by('-stock', '-updated_at')
    else:
        products = products.order_by('-updated_at', '-created_at')

    # For display stats
    total_count = products.count()
    in_stock_count = products.filter(stock__gt=0).count()
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)

    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist_product_ids = set(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    return render(request, 'pages/catalog.html', {
        'categories': categories,
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': total_count,
        'in_stock_count': in_stock_count,
        'wishlist_product_ids': wishlist_product_ids,
        'selected_category_slugs': cat_slugs,
        'catalog_querystring': query_params.urlencode(),
        'page_title': 'Product Catalog'
    })


def product_detail_view(request, product_id=None):
    # Support default product if ID is not specified
    if product_id is None:
        product = Product.objects.filter(status='ACTIVE', vendor__status='ACTIVE').first()
        if not product:
            return redirect('pages:catalog')
    else:
        product = get_object_or_404(Product, id=product_id, vendor__status='ACTIVE')

    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    reviews_count = reviews.count()

    # Related products
    related = Product.objects.filter(status='ACTIVE', vendor__status='ACTIVE', category=product.category).exclude(id=product.id)[:4]

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


def store_detail_view(request, vendor_id):
    vendor = get_object_or_404(Vendor.objects.select_related('user'), id=vendor_id)
    products = (
        Product.objects
        .filter(vendor=vendor, vendor__status='ACTIVE', status='ACTIVE')
        .select_related('category')
        .annotate(avg_rating=Avg('reviews__rating'), reviews_count=Count('reviews'))
        .order_by('-updated_at', '-created_at')
    )
    return render(request, 'pages/store_detail.html', {
        'vendor': vendor,
        'products': products,
        'page_title': vendor.store_name,
    })


@login_required(login_url='pages:login')
def profile_view(request):
    if is_admin_user(request.user):
        return redirect('pages:admin_dashboard')
    if request.user.profile.role == 'VENDOR':
        return redirect('pages:vendor_dashboard')

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
    coupon, coupon_discount, total = apply_coupon_to_total(request, subtotal)
    
    return render(request, 'pages/cart.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'total': total,
        'page_title': 'Shopping Cart'
    })


@login_required(login_url='pages:login')
def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='ACTIVE', vendor__status='ACTIVE')
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1
    
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    desired_quantity = quantity if item_created else cart_item.quantity + quantity

    # Check inventory against the final cart quantity.
    if product.stock < desired_quantity:
        messages.error(request, f"Sorry, only {product.stock} items left in stock.")
        if item_created:
            cart_item.delete()
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('pages:product_detail', product_id=product.id)

    if not item_created:
        cart_item.quantity = desired_quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.POST.get('next') or 'pages:cart')


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
@require_POST
def apply_coupon_view(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    if not code:
        request.session.pop('coupon_code', None)
        messages.info(request, "Coupon removed.")
        return redirect('pages:cart')

    coupon = Coupon.objects.filter(code=code, active=True).first()
    if not coupon:
        messages.error(request, "That coupon is not active or does not exist.")
        return redirect('pages:cart')

    now = timezone.now()
    if coupon.starts_at and coupon.starts_at > now:
        messages.error(request, "That coupon is not active yet.")
    elif coupon.expires_at and coupon.expires_at < now:
        messages.error(request, "That coupon has expired.")
    elif coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        messages.error(request, "That coupon has reached its usage limit.")
    else:
        request.session['coupon_code'] = coupon.code
        messages.success(request, f"Coupon {coupon.code} applied.")
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
    coupon, coupon_discount, total = apply_coupon_to_total(request, subtotal)
    
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
        Payment.objects.create(
            order=order,
            amount=total,
            method=payment_method,
            status='PAID',
            transaction_reference=f"PAY-{uuid.uuid4().hex[:10].upper()}",
            paid_at=timezone.now()
        )
        shipment = Shipment.objects.create(
            order=order,
            tracking_number=order.tracking_number or f"AN-{uuid.uuid4().hex[:8].upper()}"
        )
        TrackingEvent.objects.create(
            shipment=shipment,
            location="Accra Fulfillment Desk",
            description="Order placed and local mock courier shipment opened.",
        )
        Notification.objects.create(
            user=request.user,
            title='Order received',
            body=f"Order #{order.id} has been received and is being prepared.",
            notification_type='ORDER',
            link_url=f"/orders/{order.id}/"
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
            
            # Sync with Inventory model
            inventory, inv_created = Inventory.objects.get_or_create(product=item.product)
            inventory.quantity = item.product.stock
            inventory.save()
            
            # Create low stock notification for vendor if threshold is breached
            if inventory.is_low_stock:
                Notification.objects.get_or_create(
                    user=item.product.vendor.user,
                    title="Low stock alert",
                    body=f"Your product '{item.product.name}' is low on stock ({inventory.quantity} remaining).",
                    notification_type="INVENTORY",
                    link_url=f"/vendor/products/manage/{item.product.id}/"
                )

        if coupon:
            coupon.used_count += 1
            coupon.save(update_fields=['used_count'])
            request.session.pop('coupon_code', None)
            
        # Clear Cart
        cart.items.all().delete()
        
        messages.success(request, "Order placed successfully!")
        log_activity(request.user, 'ORDER_CREATED', f"Order #{order.id} created.", 'Order', order.id)
        return redirect('pages:order_confirmation', order_id=order.id)
        
    address_form = AddressForm()
    return render(request, 'pages/checkout.html', {
        'items': items,
        'addresses': addresses,
        'address_form': address_form,
        'subtotal': subtotal,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
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
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        orders = orders.filter(
            Q(id__icontains=q)
            | Q(tracking_number__icontains=q)
            | Q(items__product__name__icontains=q)
        ).distinct()
    if status in dict(Order._meta.get_field('status').choices):
        orders = orders.filter(status=status)
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="order_history.csv"'
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Date', 'Status', 'Total', 'Tracking Number', 'Products'])
        for order in orders:
            writer.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.get_status_display(),
                order.total_price,
                order.tracking_number or '',
                '; '.join(item.product.name for item in order.items.all() if item.product),
            ])
        return response
    return render(request, 'pages/order_history.html', {
        'orders': orders,
        'order_status_choices': Order._meta.get_field('status').choices,
        'selected_status': status,
        'search_query': q,
        'page_title': 'Order History'
    })


@login_required(login_url='pages:login')
def order_detail_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('address', 'payment', 'shipment').prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )
    return render(request, 'pages/order_detail.html', {'order': order, 'page_title': 'Order Details'})


@login_required(login_url='pages:login')
def order_tracking_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('shipment', 'address'),
        id=order_id,
        user=request.user
    )
    events = []
    if hasattr(order, 'shipment'):
        events = list(order.shipment.events.all())
        if not events:
            # Generate default initial event
            event = TrackingEvent.objects.create(
                shipment=order.shipment,
                location="Accra Main Terminal",
                description="Order placed and package details recorded."
            )
            events.append(event)
            # Create progress events if order status warrants it
            if order.status in ['SHIPPED', 'DELIVERED']:
                # Set created_at via helper or manual assignment after creation
                event2 = TrackingEvent.objects.create(
                    shipment=order.shipment,
                    location="Accra Distribution Hub",
                    description="Package departs Terminal, in transit."
                )
                if order.shipment.shipped_at:
                    event2.created_at = order.shipment.shipped_at
                    event2.save()
                events.append(event2)
            if order.status == 'DELIVERED':
                event3 = TrackingEvent.objects.create(
                    shipment=order.shipment,
                    location=order.address.city if order.address else "Destination",
                    description="Package delivered successfully."
                )
                if order.shipment.delivered_at:
                    event3.created_at = order.shipment.delivered_at
                    event3.save()
                events.append(event3)
    
    return render(request, 'pages/order_tracking.html', {
        'order': order,
        'events': events,
        'page_title': 'Order Tracking'
    })


@login_required(login_url='pages:login')
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__vendor', 'product__category')
    return render(request, 'pages/wishlist.html', {'items': items, 'page_title': 'Wishlist'})


@login_required(login_url='pages:login')
def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='ACTIVE', vendor__status='ACTIVE')
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"Saved {product.name} to your wishlist.")
    else:
        item.delete()
        messages.info(request, f"Removed {product.name} from your wishlist.")
    return redirect(request.POST.get('next') or 'pages:wishlist')


@login_required(login_url='pages:login')
def notifications_view(request):
    notifications = request.user.notifications.all()
    if request.method == 'POST':
        notifications.update(is_read=True)
        messages.success(request, "Notifications marked as read.")
        return redirect('pages:notifications')
    return render(request, 'pages/notifications.html', {'notifications': notifications, 'page_title': 'Notifications'})


@login_required(login_url='pages:login')
def support_tickets_view(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            Notification.objects.create(user=request.user, title='Support ticket created', body=f"Ticket #{ticket.id} is now open.", notification_type='SUPPORT')
            messages.success(request, "Support ticket opened successfully.")
            return redirect('pages:support_tickets')
    else:
        form = SupportTicketForm(user=request.user)
    tickets = request.user.support_tickets.select_related('order')
    return render(request, 'pages/support_tickets.html', {'form': form, 'tickets': tickets, 'page_title': 'Support Tickets'})


@login_required(login_url='pages:login')
def returns_view(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, user=request.user)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.save()
            messages.success(request, "Return request submitted for review.")
            return redirect('pages:returns')
    else:
        form = ReturnRequestForm(user=request.user)
    returns = request.user.return_requests.select_related('order')
    return render(request, 'pages/returns.html', {'form': form, 'returns': returns, 'page_title': 'Returns'})


@login_required(login_url='pages:login')
def payment_methods_view(request):
    payments = Payment.objects.filter(order__user=request.user).select_related('order')
    return render(request, 'pages/payment_methods.html', {'payments': payments, 'page_title': 'Payments'})


# ----------------- Vendor Views -----------------
@login_required
def vendor_dashboard_view(request):
    if request.user.profile.role != 'VENDOR':
        return redirect('pages:marketplace')

    vendor, created = Vendor.objects.get_or_create(
        user=request.user,
        defaults={
            'store_name': f"{request.user.username}'s Store"
        }
    )
    
    # Calculate statistics
    products_count = Product.objects.filter(vendor=vendor).count()
    total_stock = Product.objects.filter(vendor=vendor).aggregate(total=Sum('stock'))['total'] or 0
    total_sales = OrderItem.objects.filter(product__vendor=vendor).aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0.00
    total_orders = Order.objects.filter(items__product__vendor=vendor).distinct().count()
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(vendor=vendor).filter(
        Q(stock__lt=5) | Q(inventory__quantity__lte=F('inventory__low_stock_threshold'))
    ).distinct()
    low_stock_count = low_stock_products.count()
    
    # Recent orders processing
    recent_orders = (
        Order.objects.filter(items__product__vendor=vendor)
        .prefetch_related('items__product')
        .distinct()
        .order_by('-created_at')[:5]
    )
    for order in recent_orders:
        order.vendor_items = [item for item in order.items.all() if item.product and item.product.vendor_id == vendor.id]
        order.vendor_subtotal = sum(item.price * item.quantity for item in order.vendor_items)
        order.first_product = order.vendor_items[0].product if order.vendor_items else None

    # Latest active shipment for the vendor's products
    latest_shipment = Shipment.objects.filter(
        order__items__product__vendor=vendor
    ).select_related('order', 'order__user', 'order__address').order_by('-created_at').first()

    return render(request, 'pages/vendor_dashboard.html', {
        'vendor': vendor,
        'products_count': products_count,
        'total_stock': total_stock,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_count,
        'recent_orders': recent_orders,
        'latest_shipment': latest_shipment,
        'page_title': 'Vendor Dashboard'
    })



@login_required(login_url='pages:login')
def vendor_products_view(request):
    vendor = require_vendor(request)
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
    vendor = require_vendor(request)
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
@require_POST
def vendor_product_delete_view(request, product_id):
    vendor = require_vendor(request)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product_name = product.name
    product.delete()
    log_activity(request.user, 'PRODUCT_DELETED', f"{product_name} deleted by vendor.", 'Product', product_id)
    messages.success(request, "Product deleted.")
    return redirect('pages:vendor_products')


@login_required(login_url='pages:login')
def vendor_analytics_view(request):
    vendor = require_vendor(request)

    export_format = request.GET.get('export')
    if export_format in ['csv', 'excel', 'pdf']:
        filename_root = vendor.store_name.replace(" ", "_")
        rows = [['Date', 'Order ID', 'Product', 'Quantity', 'Price', 'Subtotal', 'Customer', 'Status']]
        items = OrderItem.objects.filter(product__vendor=vendor).select_related('order', 'order__user', 'product').order_by('-order__created_at')
        for item in items:
            subtotal = item.price * item.quantity
            rows.append([
                item.order.created_at.strftime('%Y-%m-%d %H:%M'),
                f"#{item.order.id}",
                item.product.name if item.product else "Deleted Product",
                item.quantity,
                f"GH₵ {item.price}",
                f"GH₵ {subtotal}",
                item.order.user.username,
                item.order.get_status_display()
            ])
        if export_format == 'pdf':
            response = HttpResponse(
                make_mock_pdf(f'{vendor.store_name} sales report', rows),
                content_type='application/pdf',
            )
            response['Content-Disposition'] = f'attachment; filename="{filename_root}_sales_report.pdf"'
            return response
        if export_format == 'excel':
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{filename_root}_sales_report.xls"'
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename_root}_sales_report.csv"'

        writer = csv.writer(response)
        writer.writerows(rows)
        return response

    # Dynamic KPI calculations
    total_sales = OrderItem.objects.filter(product__vendor=vendor).aggregate(total=Sum(F('price') * F('quantity')))['total'] or Decimal('0.00')
    total_orders = Order.objects.filter(items__product__vendor=vendor).distinct().count()
    
    unique_visitors = total_orders * 15 + Product.objects.filter(vendor=vendor).count() * 8 + 124
    conversion_rate = (total_orders / unique_visitors * 100) if unique_visitors > 0 else 0.0
    avg_order_value = (total_sales / total_orders) if total_orders > 0 else Decimal('0.00')
    
    # Top selling products
    top_products = Product.objects.filter(vendor=vendor).annotate(
        sold_count=Coalesce(Sum('orderitem__quantity'), 0),
        total_revenue=Coalesce(Sum(F('orderitem__price') * F('orderitem__quantity')), Decimal('0.00'))
    ).order_by('-sold_count')[:5]
    
    # Regional sales breakdown
    regional_sales = OrderItem.objects.filter(product__vendor=vendor).values(
        'order__address__region'
    ).annotate(
        order_count=Count('order', distinct=True),
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-revenue')
    
    # Filter out empty or None regions
    regional_sales = [r for r in regional_sales if r['order__address__region']]
    
    # Customer segment calculation
    order_counts = Order.objects.filter(items__product__vendor=vendor).values('user').annotate(cnt=Count('id'))
    returning_customers = sum(1 for c in order_counts if c['cnt'] > 1)
    new_customers = sum(1 for c in order_counts if c['cnt'] == 1)
    total_customers = returning_customers + new_customers
    returning_pct = int(returning_customers / total_customers * 100) if total_customers > 0 else 64
    new_pct = 100 - returning_pct

    return render(request, 'pages/vendor_analytics.html', {
        'vendor': vendor,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'unique_visitors': unique_visitors,
        'conversion_rate': conversion_rate,
        'avg_order_value': avg_order_value,
        'top_products': top_products,
        'regional_sales': regional_sales,
        'returning_pct': returning_pct,
        'new_pct': new_pct,
        'page_title': 'Vendor Analytics'
    })


@login_required(login_url='pages:login')
def vendor_orders_view(request):
    vendor = require_vendor(request)
    orders = (
        Order.objects
        .filter(items__product__vendor=vendor)
        .select_related('user', 'address', 'shipment')
        .prefetch_related('items__product')
        .distinct()
        .order_by('-created_at')
    )
    status_filter = request.GET.get('status')
    if status_filter in dict(Order._meta.get_field('status').choices):
        orders = orders.filter(status=status_filter)

    for order in orders:
        order.vendor_subtotal = order_vendor_subtotal(order, vendor)
        order.vendor_items = [item for item in order.items.all() if item.product and item.product.vendor_id == vendor.id]

    return render(request, 'pages/vendors_order_management.html', {
        'orders': orders,
        'status_filter': status_filter or '',
        'order_status_choices': Order._meta.get_field('status').choices,
        'page_title': 'Vendor Orders'
    })


@login_required(login_url='pages:login')
def vendor_order_detail_view(request, order_id):
    vendor = require_vendor(request)
    order = get_object_or_404(
        Order.objects.select_related('user', 'user__profile', 'address', 'payment', 'shipment').prefetch_related('items__product__vendor'),
        id=order_id,
        items__product__vendor=vendor,
    )
    vendor_items = [item for item in order.items.all() if item.product and item.product.vendor_id == vendor.id]
    return render(request, 'pages/vendor_order_detail.html', {
        'order': order,
        'vendor': vendor,
        'vendor_items': vendor_items,
        'vendor_subtotal': order_vendor_subtotal(order, vendor),
        'order_status_choices': Order._meta.get_field('status').choices,
        'page_title': f'Order #{order.id}',
    })


@login_required(login_url='pages:login')
@require_POST
def vendor_order_status_view(request, order_id):
    vendor = require_vendor(request)
    order = get_object_or_404(Order, id=order_id, items__product__vendor=vendor)
    status = request.POST.get('status')
    allowed_statuses = dict(Order._meta.get_field('status').choices)
    if status not in allowed_statuses:
        messages.error(request, "Choose a valid order status.")
        return redirect('pages:vendor_order_detail', order_id=order.id)

    order.status = status
    order.save(update_fields=['status'])
    shipment = getattr(order, 'shipment', None)
    if shipment:
        shipment.status = 'DELIVERED' if status == 'DELIVERED' else 'IN_TRANSIT' if status == 'SHIPPED' else shipment.status
        if status == 'SHIPPED' and not shipment.shipped_at:
            shipment.shipped_at = timezone.now()
        if status == 'DELIVERED' and not shipment.delivered_at:
            shipment.delivered_at = timezone.now()
        shipment.save()
    create_mock_tracking_event(order, status, request.user.username)
    Notification.objects.create(
        user=order.user,
        title='Order status updated',
        body=f"Order #{order.id} is now {allowed_statuses[status]}.",
        notification_type='ORDER',
        link_url=f"/orders/{order.id}/",
    )
    log_activity(request.user, 'VENDOR_ORDER_STATUS_CHANGED', f"Order #{order.id} set to {status}.", 'Order', order.id)
    messages.success(request, "Order status updated and the customer was notified.")
    return redirect(request.POST.get('next') or 'pages:vendor_order_detail', order_id=order.id)


@login_required(login_url='pages:login')
def vendor_settings_view(request):
    vendor = require_vendor(request)
    if request.method == 'POST':
        form = VendorSettingsForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            vendor = form.save(commit=False)
            if request.FILES.get('business_document'):
                vendor.business_document_uploaded_at = timezone.now()
            vendor.save()
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
    vendor = require_vendor(request)
    
    # Handle reply POST
    if request.method == 'POST' and request.POST.get('action') == 'reply':
        review_id = request.POST.get('review_id')
        reply_text = request.POST.get('reply_text', '').strip()
        review = get_object_or_404(Review, id=review_id, product__vendor=vendor)
        review.reply = reply_text
        review.replied_at = timezone.now()
        review.save()
        messages.success(request, "Your reply has been posted successfully.")
        return redirect('pages:vendor_reviews')

    reviews = Review.objects.filter(product__vendor=vendor).select_related('product', 'user').order_by('-created_at')
    
    # Review statistics
    reviews_count = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 5.0
    avg_rating = round(avg_rating, 1)
    
    # Rating counts and distribution
    rating_counts = {i: 0 for i in range(1, 6)}
    for r in reviews:
        if r.rating in rating_counts:
            rating_counts[r.rating] += 1
            
    rating_pcts = {
        i: int(count / reviews_count * 100) if reviews_count > 0 else 0
        for i, count in rating_counts.items()
    }
    
    # Response rate
    replied_count = reviews.exclude(reply__isnull=True).exclude(reply='').count()
    response_rate = round(replied_count / reviews_count * 100, 1) if reviews_count > 0 else 100.0

    return render(request, 'pages/vendor_reviews.html', {
        'vendor': vendor,
        'reviews': reviews,
        'reviews_count': reviews_count,
        'avg_rating': avg_rating,
        'rating_pcts': rating_pcts,
        'rating_counts': rating_counts,
        'response_rate': response_rate,
        'page_title': 'Vendor Reviews'
    })


@login_required(login_url='pages:login')
def vendor_coupons_view(request):
    vendor = require_vendor(request)
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.vendor = vendor
            coupon.code = coupon.code.upper()
            coupon.save()
            messages.success(request, "Coupon saved.")
            return redirect('pages:vendor_coupons')
    else:
        form = CouponForm()
    coupons = vendor.coupons.all()
    return render(request, 'pages/vendor_coupons.html', {'form': form, 'coupons': coupons, 'page_title': 'Coupons'})


@login_required(login_url='pages:login')
def vendor_payouts_view(request):
    vendor = require_vendor(request)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            payout = VendorPayout.objects.create(
                vendor=vendor,
                amount=amount,
                reference=f"PO-{uuid.uuid4().hex[:10].upper()}"
            )
            messages.success(request, f"Payout request {payout.reference} submitted.")
        except Exception:
            messages.error(request, "Enter a valid payout amount.")
        return redirect('pages:vendor_payouts')
    payouts = vendor.payouts.all()
    return render(request, 'pages/vendor_payouts.html', {'vendor': vendor, 'payouts': payouts, 'page_title': 'Payouts'})


# ----------------- Admin Views -----------------
@login_required(login_url='pages:login')
def admin_dashboard_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
        
    users_count = User.objects.count()
    vendors_count = Vendor.objects.count()
    orders_count = Order.objects.count()
    products_count = Product.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0.00
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    recent_activities = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Calculate vendor performance rankings
    vendor_rankings = Vendor.objects.annotate(
        sales_volume=Coalesce(Sum(F('products__orderitem__price') * F('products__orderitem__quantity')), Decimal('0.00')),
        rating=Coalesce(Avg('products__reviews__rating'), 5.0),
        product_count=Count('products', distinct=True)
    ).order_by('-sales_volume')[:5]
    
    return render(request, 'pages/admin_dashboard.html', {
        'users_count': users_count,
        'vendors_count': vendors_count,
        'orders_count': orders_count,
        'products_count': products_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'recent_activities': recent_activities,
        'vendor_rankings': vendor_rankings,
        'page_title': 'Admin Dashboard'
    })


@login_required(login_url='pages:login')
def admin_users_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
        
    # Handle CSV Export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="marketplace_users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Role', 'Date Joined', 'Verified', 'Status'])
        
        users = User.objects.all().select_related('profile').order_by('-date_joined')
        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.profile.role,
                user.date_joined.strftime('%Y-%m-%d'),
                'Yes' if user.profile.verified else 'No',
                'Active' if user.is_active else 'Suspended'
            ])
        return response

    # Handle Admin Creation POST
    if request.method == 'POST' and 'add_admin' in request.POST:
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if username and email and password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
                profile = user.profile
                profile.role = 'ADMIN'
                profile.verified = True
                profile.save()
                log_activity(request.user, 'ADMIN_CREATED', f"New administrator {username} created.", 'User', user.id)
                messages.success(request, f"New Administrator {username} added.")
        else:
            messages.error(request, "All fields are required to add an admin.")
        return redirect('pages:admin_users')

    # Basic search and filtering
    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()
    verification_filter = request.GET.get('verification', '').strip()

    users = User.objects.all().select_related('profile').order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) | 
            Q(email__icontains=q) | 
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q)
        )
    if role_filter:
        users = users.filter(profile__role=role_filter)
    if status_filter == 'ACTIVE':
        users = users.filter(is_active=True)
    elif status_filter == 'SUSPENDED':
        users = users.filter(is_active=False)
    if verification_filter == 'VERIFIED':
        users = users.filter(profile__verified=True)
    elif verification_filter == 'UNVERIFIED':
        users = users.filter(profile__verified=False)

    # Dynamic KPI stats
    total_users_count = User.objects.count()
    verified_users_count = UserProfile.objects.filter(verified=True).count()
    pending_users_count = UserProfile.objects.filter(verified=False).count()
    suspended_users_count = User.objects.filter(is_active=False).count()

    return render(request, 'pages/admin_users.html', {
        'users': users,
        'total_users_count': total_users_count,
        'verified_users_count': verified_users_count,
        'pending_users_count': pending_users_count,
        'suspended_users_count': suspended_users_count,
        'selected_role': role_filter,
        'selected_status': status_filter,
        'selected_verification': verification_filter,
        'search_query': q,
        'page_title': 'Admin Users'
    })


@login_required(login_url='pages:login')
@require_POST
def admin_user_action_view(request, user_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    target_user = get_object_or_404(User.objects.select_related('profile'), id=user_id)
    action = request.POST.get('action', '')

    if target_user == request.user and action in ['suspend', 'deactivate']:
        messages.error(request, "You cannot suspend your own administrator account.")
        return redirect('pages:admin_users')

    if action == 'verify':
        target_user.profile.verified = True
        target_user.profile.save(update_fields=['verified'])
        messages.success(request, f"{target_user.username} verified.")
        log_activity(request.user, 'USER_VERIFIED', f"{target_user.username} verified.", 'User', target_user.id)
    elif action == 'unverify':
        target_user.profile.verified = False
        target_user.profile.save(update_fields=['verified'])
        messages.success(request, f"{target_user.username} marked unverified.")
        log_activity(request.user, 'USER_UNVERIFIED', f"{target_user.username} unverified.", 'User', target_user.id)
    elif action == 'suspend':
        target_user.is_active = False
        target_user.save(update_fields=['is_active'])
        messages.success(request, f"{target_user.username} suspended.")
        log_activity(request.user, 'USER_SUSPENDED', f"{target_user.username} suspended.", 'User', target_user.id)
    elif action == 'activate':
        target_user.is_active = True
        target_user.save(update_fields=['is_active'])
        messages.success(request, f"{target_user.username} activated.")
        log_activity(request.user, 'USER_ACTIVATED', f"{target_user.username} activated.", 'User', target_user.id)
    elif action == 'role':
        role = request.POST.get('role')
        if role not in dict(ROLE_CHOICES := UserProfile._meta.get_field('role').choices):
            messages.error(request, "Choose a valid role.")
        else:
            target_user.profile.role = role
            target_user.profile.save(update_fields=['role'])
            target_user.is_staff = role == 'ADMIN'
            target_user.save(update_fields=['is_staff'])
            if role == 'VENDOR':
                Vendor.objects.get_or_create(user=target_user, defaults={'store_name': f"{target_user.username}'s Store"})
            messages.success(request, f"{target_user.username} role changed to {ROLE_CHOICES[role]}.")
            log_activity(request.user, 'USER_ROLE_CHANGED', f"{target_user.username} role set to {role}.", 'User', target_user.id)
    else:
        messages.error(request, "Unknown user action.")
    return redirect('pages:admin_users')


@login_required(login_url='pages:login')
def admin_vendors_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    vendors = (
        Vendor.objects
        .select_related('user')
        .annotate(product_count=Count('products'), sales_total=Coalesce(Sum('products__orderitem__price'), Decimal('0.00')))
        .order_by('-created_at')
    )
    return render(request, 'pages/admin_vendors.html', {
        'vendors': vendors,
        'verified_count': vendors.filter(verified=True).count(),
        'pending_count': vendors.filter(verified=False).count(),
        'page_title': 'Admin Vendors'
    })


@login_required(login_url='pages:login')
@require_POST
def admin_vendor_verify_view(request, vendor_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    vendor = get_object_or_404(Vendor, id=vendor_id)
    verified = request.POST.get('verified') == '1'
    vendor.verified = verified
    vendor.save(update_fields=['verified'])
    Notification.objects.create(
        user=vendor.user,
        title='Store verification updated',
        body=f"Your store has been {'approved' if verified else 'moved back to review'}.",
        notification_type='VENDOR',
        link_url='/vendor/settings/',
    )
    log_activity(request.user, 'VENDOR_VERIFICATION_CHANGED', f"{vendor.store_name} verified={verified}.", 'Vendor', vendor.id)
    messages.success(request, "Vendor verification updated.")
    return redirect('pages:admin_vendors')


@login_required(login_url='pages:login')
def admin_moderation_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    products = Product.objects.select_related('vendor', 'category').all().order_by('-created_at')
    return render(request, 'pages/admin_moderation.html', {
        'products': products,
        'active_count': products.filter(status='ACTIVE').count(),
        'draft_count': products.filter(status='DRAFT').count(),
        'page_title': 'Product Moderation'
    })


@login_required(login_url='pages:login')
def admin_orders_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    orders = Order.objects.select_related('user', 'address', 'payment', 'shipment').prefetch_related('items__product__vendor').order_by('-created_at')
    return render(request, 'pages/admin_orders.html', {
        'orders': orders,
        'order_status_choices': Order._meta.get_field('status').choices,
        'total_revenue': orders.aggregate(total=Sum('total_price'))['total'] or 0,
        'pending_payout_total': VendorPayout.objects.filter(status='REQUESTED').aggregate(total=Sum('amount'))['total'] or 0,
        'open_disputes': SupportTicket.objects.exclude(status__in=['RESOLVED', 'CLOSED']).count() + ReturnRequest.objects.exclude(status__in=['COMPLETED', 'REJECTED']).count(),
        'page_title': 'Admin Orders'
    })


@login_required(login_url='pages:login')
@require_POST
def admin_order_status_view(request, order_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status')
    allowed_statuses = dict(Order._meta.get_field('status').choices)
    if status not in allowed_statuses:
        messages.error(request, "Choose a valid order status.")
        return redirect('pages:admin_orders')
    order.status = status
    order.save(update_fields=['status'])
    shipment = create_mock_tracking_event(order, status, request.user.username)
    if status == 'SHIPPED':
        shipment.status = 'IN_TRANSIT'
        shipment.shipped_at = shipment.shipped_at or timezone.now()
        shipment.save()
    elif status == 'DELIVERED':
        shipment.status = 'DELIVERED'
        shipment.delivered_at = shipment.delivered_at or timezone.now()
        shipment.save()
    elif status == 'CANCELLED':
        shipment.status = 'RETURNED'
        shipment.save(update_fields=['status'])
    Notification.objects.create(user=order.user, title='Order status updated', body=f"Order #{order.id} is now {allowed_statuses[status]}.", notification_type='ORDER', link_url=f"/orders/{order.id}/")
    log_activity(request.user, 'ADMIN_ORDER_STATUS_CHANGED', f"Order #{order.id} set to {status}.", 'Order', order.id)
    messages.success(request, "Order status updated.")
    return redirect('pages:admin_orders')


@login_required(login_url='pages:login')
def admin_analytics_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    # Simple aggregations for graph bindings
    return render(request, 'pages/admin_analytics.html', {
        'page_title': 'Admin Analytics'
    })


@login_required(login_url='pages:login')
def admin_categories_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        icon = request.POST.get('icon', 'lucide:box').strip()
        if name and slug:
            Category.objects.update_or_create(slug=slug, defaults={'name': name, 'icon': icon})
            messages.success(request, "Category saved.")
        else:
            messages.error(request, "Name and slug are required.")
        return redirect('pages:admin_categories')
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    return render(request, 'pages/admin_categories.html', {'categories': categories, 'page_title': 'Categories'})


@login_required(login_url='pages:login')
def admin_support_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    tickets = SupportTicket.objects.select_related('user', 'order')
    returns = ReturnRequest.objects.select_related('user', 'order')
    return render(request, 'pages/admin_support.html', {'tickets': tickets, 'returns': returns, 'page_title': 'Support & Disputes'})


@login_required(login_url='pages:login')
@require_POST
def admin_ticket_status_view(request, ticket_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    status = request.POST.get('status')
    if status not in dict(SupportTicket._meta.get_field('status').choices):
        messages.error(request, "Choose a valid ticket status.")
    else:
        ticket.status = status
        ticket.save(update_fields=['status', 'updated_at'])
        if ticket.user:
            Notification.objects.create(user=ticket.user, title='Support ticket updated', body=f"Ticket #{ticket.id} is now {ticket.get_status_display()}.", notification_type='SUPPORT')
        log_activity(request.user, 'SUPPORT_TICKET_STATUS_CHANGED', f"Ticket #{ticket.id} set to {status}.", 'SupportTicket', ticket.id)
        messages.success(request, "Ticket status updated.")
    return redirect('pages:admin_support')


@login_required(login_url='pages:login')
@require_POST
def admin_return_status_view(request, return_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    return_request = get_object_or_404(ReturnRequest, id=return_id)
    status = request.POST.get('status')
    if status not in dict(ReturnRequest._meta.get_field('status').choices):
        messages.error(request, "Choose a valid return status.")
    else:
        return_request.status = status
        return_request.save(update_fields=['status', 'updated_at'])
        Notification.objects.create(user=return_request.user, title='Return request updated', body=f"Return request for order #{return_request.order_id} is now {return_request.get_status_display()}.", notification_type='RETURN')
        log_activity(request.user, 'RETURN_STATUS_CHANGED', f"Return #{return_request.id} set to {status}.", 'ReturnRequest', return_request.id)
        messages.success(request, "Return status updated.")
    return redirect('pages:admin_support')


@login_required(login_url='pages:login')
def admin_payouts_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    payouts = VendorPayout.objects.select_related('vendor', 'vendor__user')
    return render(request, 'pages/admin_payouts.html', {'payouts': payouts, 'page_title': 'Vendor Payouts'})


@login_required(login_url='pages:login')
@require_POST
def admin_payout_status_view(request, payout_id):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    payout = get_object_or_404(VendorPayout.objects.select_related('vendor__user'), id=payout_id)
    status = request.POST.get('status')
    if status not in dict(VendorPayout._meta.get_field('status').choices):
        messages.error(request, "Choose a valid payout status.")
    else:
        payout.status = status
        if status in ['PAID', 'REJECTED']:
            payout.processed_at = timezone.now()
        payout.save()
        Notification.objects.create(user=payout.vendor.user, title='Payout updated', body=f"Payout {payout.reference} is now {payout.get_status_display()}.", notification_type='PAYOUT', link_url='/vendor/payouts/')
        log_activity(request.user, 'PAYOUT_STATUS_CHANGED', f"Payout {payout.reference} set to {status}.", 'VendorPayout', payout.id)
        messages.success(request, "Payout status updated.")
    return redirect('pages:admin_payouts')


@login_required(login_url='pages:login')
def admin_activity_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    logs = ActivityLog.objects.select_related('user')[:100]
    return render(request, 'pages/admin_activity.html', {'logs': logs, 'page_title': 'Audit Logs'})


@login_required(login_url='pages:login')
def admin_settings_view(request):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    return render(request, 'pages/admin_settings.html', {'page_title': 'Site Configuration'})


@login_required(login_url='pages:login')
@require_POST
def admin_product_status_view(request, product_id, status):
    if not is_admin_user(request.user):
        return redirect('pages:marketplace')
    product = get_object_or_404(Product, id=product_id)
    if status in dict(PRODUCT_STATUS_CHOICES := Product._meta.get_field('status').choices):
        product.status = status
        product.save(update_fields=['status'])
        log_activity(request.user, 'PRODUCT_STATUS_CHANGED', f"{product.name} set to {status}.", 'Product', product.id)
        messages.success(request, "Product status updated.")
    return redirect('pages:admin_moderation')