# Upgraded UX Template Architecture

This project now has a canonical template system that future Django apps can depend on during decomposition into `accounts`, `vendors`, `products`, `orders`, `payments`, `support`, `notifications`, and `admin_panel`.

## Canonical Registry

The source of truth is:

- `pages/template_registry.py`

Views should import template paths from this registry instead of hard-coding paths. The registry defines:

- `LAYOUT_TEMPLATES`
- `PARTIAL_TEMPLATES`
- `COMPONENT_TEMPLATES`
- `BUYER_TEMPLATES`
- `VENDOR_TEMPLATES`
- `ADMIN_TEMPLATES`
- `AUTHENTICATION_TEMPLATES`
- `ERROR_TEMPLATES`
- `EMAIL_TEMPLATES`

## Layout Contract

- `layouts/base.html`: global design tokens, Tailwind, Iconify, typography, shared button/card/form utilities.
- `layouts/buyer_base.html`: buyer marketplace shell with navbar, breadcrumbs, and footer.
- `layouts/vendor_base.html`: vendor workspace shell with sidebar, sticky header, notifications, and `vendor_content`.
- `layouts/admin_base.html`: admin workspace shell with sidebar, sticky header, search, and `admin_content`.

The legacy `base.html` now extends `layouts/base.html`, so existing `pages/*` templates keep working while inheriting the upgraded visual system.

## Partial Contract

- `partials/navbar.html`
- `partials/footer.html`
- `partials/sidebar_buyer.html`
- `partials/sidebar_vendor.html`
- `partials/sidebar_admin.html`
- `partials/breadcrumbs.html`
- `partials/notifications_dropdown.html`
- `partials/search_bar.html`
- `partials/pagination.html`

## Component Contract

Product components:

- `components/product_card.html`
- `components/product_grid.html`
- `components/product_table.html`
- `components/product_filters.html`
- `components/product_search.html`
- `components/product_gallery.html`
- `components/product_reviews.html`

Order components:

- `components/order_card.html`
- `components/order_summary.html`
- `components/order_status_badge.html`
- `components/shipment_tracking.html`
- `components/invoice_component.html`

Messaging components:

- `components/message_list.html`
- `components/message_thread.html`
- `components/chat_sidebar.html`
- `components/chat_input.html`

Analytics components:

- `components/kpi_card.html`
- `components/sales_chart.html`
- `components/revenue_chart.html`
- `components/customer_chart.html`
- `components/activity_feed.html`

## Role Template Inventory

Buyer templates live in `pages/templates/buyer/`.

Vendor templates live in `pages/templates/vendor/`.

Admin templates live in `pages/templates/admin_panel/`.

Authentication templates live in `pages/templates/authentication/`.

Errors live in `pages/templates/errors/`.

Email templates live in `pages/templates/emails/`.

## Verification

The current registry was verified with Django's template loader:

- 138 registered templates
- 0 loader errors

The project also passes:

- `python3 manage.py check`
- `python3 manage.py makemigrations --check --dry-run`
