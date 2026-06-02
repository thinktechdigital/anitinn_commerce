from django.contrib import admin
from .models import UserProfile, Address, Vendor, Category, Product, Review, Cart, CartItem, Order, OrderItem

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'tier', 'verified', 'is_prime')
    list_filter = ('role', 'verified', 'is_prime')
    search_fields = ('user__username', 'user__email', 'phone_number')

class VendorAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'verified', 'balance', 'created_at')
    list_filter = ('verified',)
    search_fields = ('store_name', 'user__username', 'user__email')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'category', 'price', 'stock', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'vendor__store_name', 'description')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    inlines = [CartItemInline]
    search_fields = ('user__username',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'payment_method', 'tracking_number', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'tracking_number')
    inlines = [OrderItemInline]

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Address)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
