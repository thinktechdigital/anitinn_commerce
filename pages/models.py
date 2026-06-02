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

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
