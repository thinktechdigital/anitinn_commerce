# Anitinn Feature Activation Report

Source of truth: `docs/markdown_docs.zip` extracted to `markdown_docs/*.md`.
Audit date: 2026-06-05.

## Feature-to-Page Relationship Matrix

| Domain | Feature | Page/Template | Route | Backend | Models/Entities | Role | Status After Repair |
|---|---|---|---|---|---|---|---|
| Buyer | Marketplace/home discovery | `pages/marketplace.html` | `/` | `marketplace_view` | `Category`, `Product`, `Vendor` | Public/Buyer | Functional; hides inactive vendor stores |
| Buyer | Catalog/search/filter/sort | `pages/catalog.html` | `/catalog/` | `catalog_view` | `Category`, `Product`, `Review`, `Wishlist`, `Vendor` | Public/Buyer | Functional; hides inactive vendor stores |
| Buyer | Product detail/reviews | `pages/product_detail.html` | `/product/<id>/` | `product_detail_view` | `Product`, `Review`, `Vendor` | Public/Buyer | Functional; vendor-inactive products inaccessible |
| Buyer | Store detail | `pages/store_detail.html` | `/stores/<vendor_id>/` | `store_detail_view` | `Vendor`, `Product` | Public/Buyer | Functional; inactive stores show no active products |
| Buyer | Cart | `pages/cart.html` | `/cart/`, `/cart/add/<id>/`, `/cart/update/<id>/` | `cart_view`, `add_to_cart_view`, `update_cart_item_view` | `Cart`, `CartItem`, `Product`, `Coupon` | Buyer | Functional |
| Buyer | Checkout/local payment | `pages/checkout.html` | `/checkout/` | `checkout_view` | `Order`, `OrderItem`, `Payment`, `Shipment`, `TrackingEvent`, `Notification`, `Inventory` | Buyer | Functional; local paid payment mock |
| Buyer | Order history/search/export | `pages/order_history.html` | `/orders/` | `order_history_view` | `Order`, `OrderItem` | Buyer | Repaired; status/search filters and CSV export active |
| Buyer | Order detail | `pages/order_detail.html` | `/orders/<id>/` | `order_detail_view` | `Order`, `Payment`, `Shipment`, `OrderItem` | Buyer | Functional |
| Buyer | Shipment tracking | `pages/order_tracking.html` | `/orders/tracking/<id>/` | `order_tracking_view` | `Shipment`, `TrackingEvent` | Buyer | Repaired; local tracking events generated |
| Buyer | Wishlist | `pages/wishlist.html` | `/wishlist/`, `/wishlist/toggle/<id>/` | `wishlist_view`, `toggle_wishlist_view` | `Wishlist`, `Product` | Buyer | Functional; inactive vendor products blocked from new toggles |
| Buyer | Notifications | `pages/notifications.html` | `/notifications/` | `notifications_view` | `Notification` | Buyer/Vendor | Functional |
| Buyer | Profile/addresses | `pages/profile.html` | `/profile/` | `profile_view` | `UserProfile`, `Address` | Buyer | Functional |
| Buyer | Returns | `pages/returns.html` | `/returns/` | `returns_view` | `ReturnRequest`, `Order` | Buyer | Functional |
| Buyer | Support tickets | `pages/support_tickets.html` | `/support/tickets/` | `support_tickets_view` | `SupportTicket`, `Order`, `Notification` | Buyer | Functional |
| Buyer | Payment records | `pages/payment_methods.html` | `/payments/` | `payment_methods_view` | `Payment`, `Order` | Buyer | Functional |
| Vendor | Dashboard KPIs | `pages/vendor_dashboard.html` | `/vendor/` | `vendor_dashboard_view` | `Vendor`, `Product`, `Inventory`, `Order`, `OrderItem`, `Shipment` | Vendor | Functional |
| Vendor | Product CRUD | `pages/vendor_products.html`, `pages/vendor_product_form.html` | `/vendor/products/`, `/vendor/products/manage/`, delete route | `vendor_products_view`, `vendor_product_form_view`, `vendor_product_delete_view` | `Product`, `Category`, `Inventory` | Vendor | Functional |
| Vendor | Order management | `pages/vendors_order_management.html`, `pages/vendor_order_detail.html` | `/vendor/orders/`, `/vendor/orders/<id>/`, status route | `vendor_orders_view`, `vendor_order_detail_view`, `vendor_order_status_view` | `Order`, `OrderItem`, `Shipment`, `TrackingEvent`, `Notification` | Vendor | Repaired; status updates generate mock tracking events |
| Vendor | Reviews/replies/analytics | `pages/vendor_reviews.html` | `/vendor/reviews/` | `vendor_reviews_view` | `Review` | Vendor | Functional |
| Vendor | Analytics/report export | `pages/vendor_analytics.html` | `/vendor/analytics/` | `vendor_analytics_view` | `OrderItem`, `Product`, `Order`, `Address` | Vendor | Repaired; CSV, Excel `.xls`, and valid mock PDF exports active |
| Vendor | Coupons | `pages/vendor_coupons.html` | `/vendor/coupons/` | `vendor_coupons_view` | `Coupon` | Vendor | Functional |
| Vendor | Payout requests | `pages/vendor_payouts.html` | `/vendor/payouts/` | `vendor_payouts_view` | `VendorPayout`, `Vendor` | Vendor | Functional |
| Vendor | Settings/document upload/danger zone | `pages/vendor_settings.html` | `/vendor/settings/` | `vendor_settings_view` | `Vendor` | Vendor | Repaired; multipart local document upload and ACTIVE/SUSPENDED/ARCHIVED/DELETED status active |
| Admin | Dashboard | `pages/admin_dashboard.html` | `/admin-panel/` | `admin_dashboard_view` | `User`, `Vendor`, `Order`, `Product`, `ActivityLog` | ADMIN | Functional |
| Admin | User management | `pages/admin_users.html` | `/admin-panel/users/`, user action route | `admin_users_view`, `admin_user_action_view` | `User`, `UserProfile`, `Vendor`, `ActivityLog` | ADMIN | Repaired; CSV, add admin, filters, verify/suspend/activate/change role active |
| Admin | Vendor management | `pages/admin_vendors.html` | `/admin-panel/vendors/`, verify route | `admin_vendors_view`, `admin_vendor_verify_view` | `Vendor`, `Notification`, `ActivityLog` | ADMIN | Functional |
| Admin | Product moderation | `pages/admin_moderation.html` | `/admin-panel/moderation/`, product status route | `admin_moderation_view`, `admin_product_status_view` | `Product`, `Vendor`, `Category`, `ActivityLog` | ADMIN | Repaired; approve, reject-to-DRAFT, flag moderation active via POST |
| Admin | Order oversight | `pages/admin_orders.html` | `/admin-panel/orders/`, status route | `admin_orders_view`, `admin_order_status_view` | `Order`, `Payment`, `Shipment`, `TrackingEvent`, `VendorPayout`, `SupportTicket`, `ReturnRequest` | ADMIN | Repaired; status creates local tracking events |
| Admin | Categories | `pages/admin_categories.html` | `/admin-panel/categories/` | `admin_categories_view` | `Category` | ADMIN | Functional |
| Admin | Support/returns | `pages/admin_support.html` | `/admin-panel/support/`, status routes | `admin_support_view`, `admin_ticket_status_view`, `admin_return_status_view` | `SupportTicket`, `ReturnRequest`, `Notification`, `ActivityLog` | ADMIN | Functional |
| Admin | Payout control | `pages/admin_payouts.html` | `/admin-panel/payouts/`, status route | `admin_payouts_view`, `admin_payout_status_view` | `VendorPayout`, `Notification`, `ActivityLog` | ADMIN | Functional |
| Admin | Activity/audit | `pages/admin_activity.html` | `/admin-panel/activity/` | `admin_activity_view` | `ActivityLog` | ADMIN | Functional |
| Admin | Settings | `pages/admin_settings.html` | `/admin-panel/settings/` | `admin_settings_view` | Static config page | ADMIN | Partial; no persisted platform settings model in ZIP requirements |

## Defect and Gap Analysis

| Area | Before | Repair/Decision | After |
|---|---|---|---|
| Admin user management | ZIP identified CSV export, add admin, filters, search as broken; template was largely static and actions were buttons only | Rebuilt page around real query filters, CSV export, add-admin POST, and per-user action forms | Functional and ADMIN-only |
| Admin user permissions | `is_staff` or `ADMIN` profile could enter admin pages | Clarified policy accepted: only admin managers should perform actions; action routes enforce `is_admin_user` and create ADMIN profiles via controlled POST | Functional; guarded at route level |
| Product moderation | Static cards and dead Approve/Reject buttons | Replaced with database products and POST forms; reject maps to `DRAFT` so product is removed from marketplace without DB deletion | Functional |
| Vendor analytics export | CSV existed, Excel/PDF missing | Added local/mock Excel `.xls` and valid minimal PDF export | Functional |
| Shipment tracking | Tracking page could generate initial events lazily; status changes did not consistently append events | Added shared local mock tracking event generator and called it from vendor/admin status updates and checkout | Functional |
| Vendor settings upload | Business Registration Upload was static | Added `Vendor.business_document`, timestamp, form file input, multipart template, and migration | Functional local upload |
| Vendor danger zone | Static pause/deactivate buttons | Converted danger zone into persisted store `status` selector: ACTIVE/SUSPENDED/ARCHIVED/DELETED | Functional |
| Store-status visibility | Suspended/deleted vendor products could still appear if product was ACTIVE | Buyer marketplace/catalog/product/cart/wishlist now require active vendor stores | Functional |
| Order history filters/export | Tabs/search/download were UI-only | Added GET filters/search and CSV export | Functional |
| Platform settings | ZIP lists shipping/payments/commissions/notifications/security/feature toggles | No model/business rules exist for persisted platform settings | Still partial; requires requirements before DB schema/workflow creation |
| External integrations | Courier, payment, PDF/Excel, documents | User approved local/mock implementations | Mocked locally; no external dependencies |

## Repaired and Activated Features

- ADMIN-only user CSV export, add-admin, search/filter, verify/unverify, suspend/activate, and role-change workflows.
- Product moderation approve, reject-to-draft, and flag-for-review actions.
- Vendor analytics CSV, Excel, and valid mock PDF exports.
- Local tracking events for checkout plus vendor/admin order status changes.
- Vendor settings local business document upload and persisted payout/shipping/subscription/status settings.
- Vendor danger-zone statuses and buyer-facing suppression of inactive vendor products.
- Buyer order-history search/status filters and CSV download.

## Verification Report

| Check | Result |
|---|---|
| `python manage.py check` | Passed, no issues |
| `python manage.py migrate` | Applied `pages.0005_vendor_business_document_and_more` successfully |
| Admin users render | `/admin-panel/users/` returned 200 |
| Admin moderation render | `/admin-panel/moderation/` returned 200 |
| Vendor settings render | `/vendor/settings/` returned 200 |
| Admin verify user | POST returned 302 and target profile became verified |
| Admin product approve | POST returned 302 and product status became `ACTIVE` |
| Admin product reject | POST returned 302 and product status became `DRAFT` |
| Admin CSV export | Returned 200 `text/csv` |
| Vendor CSV export | Returned 200 `text/csv` |
| Vendor Excel export | Returned 200 `application/vnd.ms-excel` |
| Vendor PDF export | Returned 200 `application/pdf` with `%PDF-1.4` header |
| Vendor document upload/status | POST returned 302, uploaded file persisted, store status became `SUSPENDED` |
| Buyer order filters/export | `/orders/?q=Probe&status=PENDING` returned 200; CSV returned 200 `text/csv` |
| Store-status suppression | Suspended vendor product was absent from catalog search results |
| Admin order status tracking | POST returned 302 and tracking event existed for order shipment |

## Remaining Requirement-Dependent Gaps

- Persistent platform settings need explicit fields, validation, and business rules.
- Real external courier/payment gateways are intentionally not integrated; current behavior is local/mock per instruction.
- Product rejection currently preserves records as `DRAFT`; hard deletion/removal is intentionally avoided for auditability.
