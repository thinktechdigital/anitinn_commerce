# Navigation Audit

This project now treats navigation as role-based instead of page-by-page.

## Customer Menu

Customer-facing pages should lead back to shopping and account tasks:

- Marketplace
- Catalog
- Wishlist
- Cart
- Orders
- Payment Methods
- Returns
- Support Tickets
- Notifications
- Profile

## Vendor Menu

Vendor dashboard pages should focus on store operations:

- Dashboard
- Products
- Orders
- Analytics
- Reviews
- Discounts
- Store Settings
- Payouts, where finance is the page focus
- Logout

## Admin Menu

Admin pages share `partials/admin_sidebar.html` as the source of truth:

- Dashboard
- Users
- Vendors
- Product Moderation
- Orders
- Analytics
- Categories
- Support
- Activity
- Settings
- Logout

## Link Policy

External Superdesign preview links and dead `href="#"` placeholders should not be committed into app templates. Use named Django routes with `{% url 'pages:route_name' %}` so templates continue to work when URLs change.
