from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    # General & Buyer Views
    path("vendor_dashboard/", views.vendor_dashboard_view, name="vendor_dashboard"),
    path("", views.marketplace_view, name="marketplace"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("product/", views.product_detail_view, name="product_detail_default"),
    path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart_view, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item_view, name="update_cart_item"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("order/confirmation/<int:order_id>/", views.order_confirmation_view, name="order_confirmation"),
    path("orders/", views.order_history_view, name="order_history"),
    path("orders/tracking/<int:order_id>/", views.order_tracking_view, name="order_tracking"),
    path("profile/", views.profile_view, name="profile"),
    
    # Auth Views
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    
    # Static Informational Pages
    path("help/", views.make_static_view("pages/help.html", "Help Center"), name="help"),
    path("password-reset/", views.make_static_view("pages/password_reset.html", "Reset Password"), name="password_reset"),
    path("password-reset/confirm/", views.make_static_view("pages/password_reset_confirm.html", "Confirm Password Reset"), name="password_reset_confirm"),
    path("terms/", views.make_static_view("pages/terms.html", "Terms of Service"), name="terms"),
    path("privacy/", views.make_static_view("pages/privacy.html", "Privacy Policy"), name="privacy"),
    path("contact/", views.make_static_view("pages/contact.html", "Contact Us"), name="contact"),
    
    # Vendor Views
    path("vendor/products/", views.vendor_products_view, name="vendor_products"),
    path("vendor/products/manage/", views.vendor_product_form_view, name="vendor_product_form"),
    path("vendor/products/manage/<int:product_id>/", views.vendor_product_form_view, name="vendor_product_edit"),
    path("vendor/analytics/", views.vendor_analytics_view, name="vendor_analytics"),
    path("vendor/settings/", views.vendor_settings_view, name="vendor_settings"),
    path("vendor/orders/", views.vendor_orders_view, name="vendor_orders"),
    path("vendor/reviews/", views.vendor_reviews_view, name="vendor_reviews"),
    
    # Admin Views
    path("admin-panel/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_users_view, name="admin_users"),
    path("admin-panel/vendors/", views.admin_vendors_view, name="admin_vendors"),
    path("admin-panel/moderation/", views.admin_moderation_view, name="admin_moderation"),
    path("admin-panel/orders/", views.admin_orders_view, name="admin_orders"),
    path("admin-panel/analytics/", views.admin_analytics_view, name="admin_analytics"),
]
