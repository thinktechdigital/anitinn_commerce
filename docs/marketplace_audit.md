# Anitinn Marketplace Audit

## Existing Structure

- Django project: `anitinn`
- Django apps: `pages`
- Primary routing: `anitinn/urls.py` includes `pages.urls`
- Templates: `pages/templates/base.html` plus page templates under `pages/templates/pages/`
- Static/media: `static/`, `media/`, `media/logo.png`
- Database: SQLite for local development
- Authentication: Django `User`, custom `UserProfile` roles, login/register/logout views
- Roles: `BUYER`, `VENDOR`, `ADMIN`; admin also allows `is_staff`
- Dashboards: buyer profile/account pages, vendor dashboard/catalog operations, admin dashboard/moderation/management pages

## Existing Models

- Account and identity: `UserProfile`, `Address`
- Vendor and catalog: `Vendor`, `Category`, `Product`, `ProductImage`, `Inventory`
- Commerce: `Cart`, `CartItem`, `Wishlist`, `Order`, `OrderItem`, `Payment`, `Shipment`, `Coupon`
- Engagement and operations: `Review`, `Notification`, `SupportTicket`, `ReturnRequest`, `VendorPayout`, `ActivityLog`

## Existing Forms

- `UserRegisterForm`, `UserLoginForm`, `UserProfileForm`, `AddressForm`
- `ProductForm`, `VendorSettingsForm`, `ReviewForm`
- `SupportTicketForm`, `CouponForm`, `ReturnRequestForm`

## Existing Views And Workflows

- Buyer: marketplace, catalog search/filter/sort, product detail, reviews, cart, checkout, order confirmation, order history, order detail, tracking, wishlist, notifications, support tickets, returns, payments, profile/address management
- Vendor: dashboard, product listing, create/edit product, analytics, orders, reviews, coupons, payouts, store settings
- Admin: dashboard, users, vendors, product moderation/status changes, orders, analytics, categories, support/disputes, activity logs, settings

## UI/UX Audit

- Visual system: Tailwind CDN, Plus Jakarta Sans, royal green, golden yellow, warm white, Iconify icons.
- Strengths: coherent marketplace branding, clear buyer commerce flow, role-specific dashboards, empty states on newer account pages.
- Risks: several older dashboard templates contain hard-coded prototype links, static metrics, and Vue-style attributes without a Vue runtime. These do not break Django template loading, but should be replaced with Django URL tags and live context values before production.
- Accessibility: forms use visible labels in newer templates; older templates need a pass for semantic headings, focus states, and meaningful alt text.
- Mobile responsiveness: buyer pages are mostly responsive; vendor/admin sidebar layouts are desktop-first and need mobile drawer behavior for production.
- Error/loading states: form validation and messages exist; loading states are mostly absent because the app is server-rendered.

## Gap Analysis

### Implemented

- Role-based registration and dashboard redirection
- Product browsing, search, filters, sorting
- Cart and checkout with order, payment, shipment, notification creation
- Buyer order history, detail, tracking, wishlist, returns, support, notifications, payment history
- Vendor product CRUD, settings, order view, review view, coupons, payouts
- Admin users, vendors, orders, product moderation, categories, support/disputes, audit logs
- Django admin registration for marketplace models

### Partially Implemented

- Account activation and password reset pages are static, not token-email workflows.
- Vendor approval is represented by `Vendor.verified`, but no approve/reject action workflow is implemented in the custom admin pages.
- Inventory exists as a model, while most cart/checkout logic still reads and updates `Product.stock`.
- Payment is simulated as immediately paid; no real payment gateway exists.
- Shipping is simulated with shipment records and status fields; no carrier integration exists.
- Analytics pages exist, but much of the UI is static rather than data-driven.
- Product images support multiple records, but forms currently use a single `image_url`.

### Missing Or Production-Risk Items

- Email verification, password reset email delivery, and secure account activation.
- Object-level action controls for admin support tickets, returns, vendor approvals, order status changes, and payouts.
- Vendor store public page and store customization preview.
- Real payment provider integration, webhook handling, idempotency, refunds, and reconciliation.
- Coupon application during cart/checkout.
- Full inventory reservation, oversell prevention, and order cancellation restocking.
- Pagination for catalog, admin, vendor, audit, support, and order listings.
- Tests for permissions, checkout, stock changes, vendor ownership, admin-only routes, and form validation.
- Production settings for secrets, database, static file serving, logging, CSRF/secure cookies, allowed hosts, and email backend.

## Missing Page Inventory After This Pass

The existing URL map now has matching templates for the custom pages it references. Remaining recommended production pages/workflows are:

| Page or Workflow | Role | Suggested URL | Required Work |
| --- | --- | --- | --- |
| Account activation | Buyer/Vendor | `/accounts/activate/<token>/` | Token model or signed token, email templates, activation view |
| Password reset workflow | Buyer/Vendor/Admin | `/password-reset/` | Use Django auth reset views and email backend |
| Public store page | Buyer/Vendor | `/stores/<slug>/` | Store slug, vendor storefront template, product list |
| Vendor approval actions | Admin | `/admin-panel/vendors/<id>/approve/` | POST action, permission check, activity log |
| Order status management | Vendor/Admin | `/vendor/orders/<id>/status/`, `/admin-panel/orders/<id>/status/` | Status form, ownership validation, notifications |
| Payout approval | Admin | `/admin-panel/payouts/` | Payout queue, approve/reject actions, processed timestamps |
| Coupon application | Buyer | `/cart/apply-coupon/` | Cart/session coupon state, validation, checkout totals |
| Support ticket detail | Buyer/Admin | `/support/tickets/<id>/`, `/admin-panel/support/<id>/` | Thread/detail model or response fields |
| Return detail/actions | Buyer/Admin | `/returns/<id>/`, `/admin-panel/returns/<id>/status/` | Detail view, status transitions |
| Platform CMS/settings forms | Admin | `/admin-panel/settings/` | Settings model, forms, validation |

## Journey Maps

### Buyer

Registration -> login -> marketplace/catalog -> product detail -> add to cart -> checkout -> payment record -> order confirmation -> order detail/tracking -> review/return/support.

Main remaining gaps: activation, real payment, coupon application, richer support conversations, review eligibility rules.

### Vendor

Registration as vendor -> vendor dashboard -> configure store -> create/edit products -> receive orders -> monitor reviews and analytics -> create coupons -> request payouts.

Main remaining gaps: approval gating, public store page, inventory operations, order fulfillment actions, payout processing.

### Administrator

Login as staff or `ADMIN` profile -> dashboard -> user/vendor management -> product moderation -> order monitoring -> support/dispute review -> category management -> audit logs/settings.

Main remaining gaps: action endpoints for approvals/status changes, dispute resolution lifecycle, configurable platform settings, report exports.

## Sitemap

- Public: `/`, `/catalog/`, `/product/<id>/`, `/help/`, `/terms/`, `/privacy/`, `/contact/`
- Accounts: `/register/`, `/login/`, `/logout/`, `/profile/`, `/password-reset/`
- Buyer: `/cart/`, `/checkout/`, `/orders/`, `/orders/<id>/`, `/orders/tracking/<id>/`, `/wishlist/`, `/notifications/`, `/payments/`, `/returns/`, `/support/tickets/`
- Vendor: `/vendor/`, `/vendor/products/`, `/vendor/products/manage/`, `/vendor/orders/`, `/vendor/analytics/`, `/vendor/reviews/`, `/vendor/coupons/`, `/vendor/payouts/`, `/vendor/settings/`
- Admin: `/admin-panel/`, `/admin-panel/users/`, `/admin-panel/vendors/`, `/admin-panel/moderation/`, `/admin-panel/orders/`, `/admin-panel/analytics/`, `/admin-panel/categories/`, `/admin-panel/support/`, `/admin-panel/activity/`, `/admin-panel/settings/`

## Verification

- Added templates for previously disconnected routes:
  - `vendor_coupons.html`
  - `vendor_payouts.html`
  - `admin_categories.html`
  - `admin_support.html`
  - `admin_activity.html`
  - `admin_settings.html`
- Added migration `pages.0002` for marketplace models that existed in `models.py` but were not yet represented in migrations.
- Verified with:
  - `python3 manage.py check`
  - `python3 manage.py makemigrations --check --dry-run`
  - `python3 manage.py migrate`
  - Django template loader compilation for the six added templates
