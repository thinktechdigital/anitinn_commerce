from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_CHOICES = (
    ('BUYER', 'Buyer'),
    ('VENDOR', 'Vendor'),
    ('ADMIN', 'Admin'),
)

ADDRESS_TYPE_CHOICES = (
    ('HOME', 'Home'),
    ('WORK', 'Work'),
    ('OTHER', 'Other'),
)

PRODUCT_STATUS_CHOICES = (
    ('ACTIVE', 'Active'),
    ('DRAFT', 'Draft'),
    ('MODERATION', 'Moderation'),
)

ORDER_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
)

TICKET_STATUS_CHOICES = (
    ('OPEN', 'Open'),
    ('IN_PROGRESS', 'In progress'),
    ('RESOLVED', 'Resolved'),
    ('CLOSED', 'Closed'),
)

PAYMENT_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('PAID', 'Paid'),
    ('FAILED', 'Failed'),
    ('REFUNDED', 'Refunded'),
)

SHIPMENT_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('PACKED', 'Packed'),
    ('IN_TRANSIT', 'In transit'),
    ('DELIVERED', 'Delivered'),
    ('RETURNED', 'Returned'),
)

PAYOUT_STATUS_CHOICES = (
    ('REQUESTED', 'Requested'),
    ('PROCESSING', 'Processing'),
    ('PAID', 'Paid'),
    ('REJECTED', 'Rejected'),
)

RETURN_STATUS_CHOICES = (
    ('REQUESTED', 'Requested'),
    ('REVIEWING', 'Reviewing'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('COMPLETED', 'Completed'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='BUYER')
    phone_number = models.CharField(max_length=20, blank=True)
    birthday = models.DateField(null=True, blank=True)
    avatar_url = models.CharField(max_length=255, default="https://api.dicebear.com/7.x/avataaars/svg?seed=Ama")
    tier = models.CharField(max_length=50, default='Standard Buyer')
    verified = models.BooleanField(default=False)
    is_prime = models.BooleanField(default=False)
    hub = models.CharField(max_length=100, default='Accra Hub 1')

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='HOME')
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Ghana')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.address_type} - {self.street_address}, {self.city}"


class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    store_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo_url = models.CharField(max_length=255, blank=True)
    banner_url = models.CharField(max_length=255, blank=True)
    verified = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Extended settings fields
    tin = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    primary_brand_color = models.CharField(max_length=20, default='#1B5E3F')
    accent_brand_color = models.CharField(max_length=20, default='#D4A520')
    payout_method = models.CharField(max_length=20, default='MOMO')
    momo_number = models.CharField(max_length=20, blank=True)
    momo_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_account_name = models.CharField(max_length=100, blank=True)
    self_shipping_mode = models.BooleanField(default=False)
    subscription_tier = models.CharField(max_length=20, default='Standard')
    status = models.CharField(max_length=20, default='ACTIVE')
    business_document = models.FileField(upload_to='vendor_documents/', blank=True, null=True)
    business_document_uploaded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.store_name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='lucide:box')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.CharField(max_length=255, blank=True)
    stock = models.IntegerField(default=0)
    status = models.CharField(max_length=15, choices=PRODUCT_STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def available_stock(self):
        inventory = getattr(self, 'inventory', None)
        return inventory.quantity if inventory else self.stock


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Seller reply
    reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_wishlist_product')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.product.name}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, blank=True)
    tracking_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Purchase price captured at order time
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Order #{self.order.id})"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    transaction_reference = models.CharField(max_length=100, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_reference} ({self.status})"


class Shipment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=100, default='Anitinn Logistics')
    tracking_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=15, choices=SHIPMENT_STATUS_CHOICES, default='PENDING')
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment {self.tracking_number}"


class TrackingEvent(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    location = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.location} - {self.description} ({self.created_at})"


class Coupon(models.Model):
    PERCENT = 'PERCENT'
    FIXED = 'FIXED'
    DISCOUNT_CHOICES = ((PERCENT, 'Percent'), (FIXED, 'Fixed amount'))

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='coupons', null=True, blank=True)
    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_CHOICES, default=PERCENT)
    value = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=0, help_text='0 means unlimited')
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    body = models.TextField()
    notification_type = models.CharField(max_length=40, default='GENERAL')
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SupportTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    subject = models.CharField(max_length=160)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=TICKET_STATUS_CHOICES, default='OPEN')
    priority = models.CharField(max_length=10, choices=(('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High')), default='NORMAL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.subject


class ReturnRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    reason = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=RETURN_STATUS_CHOICES, default='REQUESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return request for order #{self.order_id}"


class VendorPayout(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=15, choices=PAYOUT_STATUS_CHOICES, default='REQUESTED')
    reference = models.CharField(max_length=100, unique=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.vendor.store_name} payout {self.reference}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=80)
    actor_role = models.CharField(max_length=20, blank=True)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.action


# Django signals to auto-create profile and cart when a new User is created
@receiver(post_save, sender=User)
def create_user_profile_and_cart(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Cart.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Product)
def create_or_update_product_inventory(sender, instance, created, **kwargs):
    inventory, _ = Inventory.objects.get_or_create(product=instance)
    inventory.quantity = instance.stock
    inventory.save()
