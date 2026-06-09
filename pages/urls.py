from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [

    # General & Buyer Views
    path("vendor/", views.vendor_dashboard_view, name="vendor_dashboard"),
    path("", views.marketplace_view, name="marketplace"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("product/", views.product_detail_view, name="product_detail_default"),
    path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),
    path("stores/<int:vendor_id>/", views.store_detail_view, name="store_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart_view, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item_view, name="update_cart_item"),
    path("cart/apply-coupon/", views.apply_coupon_view, name="apply_coupon"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("order/confirmation/<int:order_id>/", views.order_confirmation_view, name="order_confirmation"),
    path("orders/", views.order_history_view, name="order_history"),
    path("orders/<int:order_id>/", views.order_detail_view, name="order_detail"),
    path("orders/tracking/<int:order_id>/", views.order_tracking_view, name="order_tracking"),
    path("profile/", views.profile_view, name="profile"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist_view, name="toggle_wishlist"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("support/tickets/", views.support_tickets_view, name="support_tickets"),
    path("returns/", views.returns_view, name="returns"),
    path("payments/", views.payment_methods_view, name="payment_methods"),
    
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
    path("vendor/products/<int:product_id>/delete/", views.vendor_product_delete_view, name="vendor_product_delete"),
    path("vendor/analytics/", views.vendor_analytics_view, name="vendor_analytics"),
    path("vendor/settings/", views.vendor_settings_view, name="vendor_settings"),
    path("vendor/orders/", views.vendor_orders_view, name="vendor_orders"),
    path("vendor/orders/<int:order_id>/", views.vendor_order_detail_view, name="vendor_order_detail"),
    path("vendor/orders/<int:order_id>/status/", views.vendor_order_status_view, name="vendor_order_status"),
    path("vendor/reviews/", views.vendor_reviews_view, name="vendor_reviews"),
    path("vendor/coupons/", views.vendor_coupons_view, name="vendor_coupons"),
    path("vendor/payouts/", views.vendor_payouts_view, name="vendor_payouts"),
    
    # Admin Views
    path("admin-panel/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_users_view, name="admin_users"),
    path("admin-panel/users/<int:user_id>/action/", views.admin_user_action_view, name="admin_user_action"),
    path("admin-panel/vendors/", views.admin_vendors_view, name="admin_vendors"),
    path("admin-panel/vendors/<int:vendor_id>/verify/", views.admin_vendor_verify_view, name="admin_vendor_verify"),
    path("admin-panel/moderation/", views.admin_moderation_view, name="admin_moderation"),
    path("admin-panel/orders/", views.admin_orders_view, name="admin_orders"),
    path("admin-panel/orders/<int:order_id>/status/", views.admin_order_status_view, name="admin_order_status"),
    path("admin-panel/analytics/", views.admin_analytics_view, name="admin_analytics"),
    path("admin-panel/categories/", views.admin_categories_view, name="admin_categories"),
    path("admin-panel/support/", views.admin_support_view, name="admin_support"),
    path("admin-panel/support/tickets/<int:ticket_id>/status/", views.admin_ticket_status_view, name="admin_ticket_status"),
    path("admin-panel/support/returns/<int:return_id>/status/", views.admin_return_status_view, name="admin_return_status"),
    path("admin-panel/payouts/", views.admin_payouts_view, name="admin_payouts"),
    path("admin-panel/payouts/<int:payout_id>/status/", views.admin_payout_status_view, name="admin_payout_status"),
    path("admin-panel/activity/", views.admin_activity_view, name="admin_activity"),
    path("admin-panel/settings/", views.admin_settings_view, name="admin_settings"),
    path("admin-panel/products/<int:product_id>/<str:status>/", views.admin_product_status_view, name="admin_product_status"),
]
