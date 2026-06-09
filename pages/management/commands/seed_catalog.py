from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from pages.models import Category, Product, Vendor


class Command(BaseCommand):
    help = "Seed the catalog with active sample products using public Unsplash image URLs."

    def handle(self, *args, **options):
        vendor_user, _ = User.objects.get_or_create(
            username="anitinn_sample_vendor",
            defaults={"email": "vendor@example.com"},
        )
        vendor_user.set_unusable_password()
        vendor_user.save(update_fields=["password"])
        vendor_user.profile.role = "VENDOR"
        vendor_user.profile.save(update_fields=["role"])

        vendor, _ = Vendor.objects.get_or_create(
            user=vendor_user,
            defaults={
                "store_name": "Anitinn Sample Store",
                "description": "Curated sample products for the Anitinn catalog.",
                "verified": True,
            },
        )

        categories = {
            "electronics": Category.objects.update_or_create(
                slug="electronics",
                defaults={"name": "Electronics", "icon": "lucide:smartphone"},
            )[0],
            "home-living": Category.objects.update_or_create(
                slug="home-living",
                defaults={"name": "Home & Living", "icon": "lucide:sofa"},
            )[0],
            "fashion": Category.objects.update_or_create(
                slug="fashion",
                defaults={"name": "Fashion", "icon": "lucide:shirt"},
            )[0],
            "beauty": Category.objects.update_or_create(
                slug="beauty",
                defaults={"name": "Beauty", "icon": "lucide:sparkles"},
            )[0],
        }

        products = [
            {
                "name": "Wireless Noise Cancelling Headphones",
                "category": "electronics",
                "price": "899.00",
                "compare_at_price": "1199.00",
                "stock": 18,
                "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?q=80&w=1200&auto=format&fit=crop",
                "description": "Comfortable wireless headphones with deep bass, active noise cancellation, and all-day battery life.",
            },
            {
                "name": "Smart Fitness Watch",
                "category": "electronics",
                "price": "650.00",
                "compare_at_price": "820.00",
                "stock": 24,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1200&auto=format&fit=crop",
                "description": "A lightweight smartwatch with activity tracking, notifications, and a bright touch display.",
            },
            {
                "name": "Ultra Slim Laptop Stand",
                "category": "electronics",
                "price": "175.00",
                "compare_at_price": None,
                "stock": 32,
                "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?q=80&w=1200&auto=format&fit=crop",
                "description": "Foldable aluminum stand for laptops and tablets, built for ergonomic desk setups.",
            },
            {
                "name": "Mechanical Keyboard RGB",
                "category": "electronics",
                "price": "420.00",
                "compare_at_price": "560.00",
                "stock": 15,
                "image_url": "https://images.unsplash.com/photo-1527814050087-3793815479db?q=80&w=1200&auto=format&fit=crop",
                "description": "Tactile mechanical keyboard with RGB backlighting and compact productivity layout.",
            },
            {
                "name": "Ceramic Dinnerware Set",
                "category": "home-living",
                "price": "340.00",
                "compare_at_price": "410.00",
                "stock": 12,
                "image_url": "https://images.unsplash.com/photo-1603199506016-b9a594b593c0?q=80&w=1200&auto=format&fit=crop",
                "description": "Minimal ceramic plates and bowls for polished everyday dining.",
            },
            {
                "name": "Modern Desk Lamp",
                "category": "home-living",
                "price": "220.00",
                "compare_at_price": None,
                "stock": 20,
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?q=80&w=1200&auto=format&fit=crop",
                "description": "Adjustable desk lamp with warm light for workspaces, reading corners, and bedside tables.",
            },
            {
                "name": "Classic Leather Backpack",
                "category": "fashion",
                "price": "480.00",
                "compare_at_price": "620.00",
                "stock": 14,
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop",
                "description": "Durable daily backpack with a premium look and practical compartments.",
            },
            {
                "name": "Minimal Everyday Sneakers",
                "category": "fashion",
                "price": "390.00",
                "compare_at_price": None,
                "stock": 27,
                "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?q=80&w=1200&auto=format&fit=crop",
                "description": "Clean, versatile sneakers for work, weekend errands, and casual outings.",
            },
            {
                "name": "Hydrating Skincare Set",
                "category": "beauty",
                "price": "260.00",
                "compare_at_price": "330.00",
                "stock": 21,
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1200&auto=format&fit=crop",
                "description": "A gentle skincare set with cleanser, serum, and moisturizer for daily routines.",
            },
            {
                "name": "Premium Fragrance Bottle",
                "category": "beauty",
                "price": "520.00",
                "compare_at_price": None,
                "stock": 9,
                "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?q=80&w=1200&auto=format&fit=crop",
                "description": "Elegant fragrance with warm, fresh notes and a polished bottle design.",
            },
        ]

        created = 0
        updated = 0
        for data in products:
            defaults = {
                "vendor": vendor,
                "category": categories[data["category"]],
                "description": data["description"],
                "price": Decimal(data["price"]),
                "compare_at_price": Decimal(data["compare_at_price"]) if data["compare_at_price"] else None,
                "image_url": data["image_url"],
                "stock": data["stock"],
                "status": "ACTIVE",
            }
            _, was_created = Product.objects.update_or_create(
                name=data["name"],
                vendor=vendor,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded catalog: {created} created, {updated} updated."))
