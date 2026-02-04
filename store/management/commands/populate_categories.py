from django.core.management.base import BaseCommand
from store.models import Category


class Command(BaseCommand):
    help = 'Populate database with initial categories'

    def handle(self, *args, **kwargs):
        categories = [
            "Women's Apparel",
            "Mobile & Gadgets",
            "Computers & Peripherals",
            "Home Appliances",
            "Food & Beverages",
            "Kids Fashion",
            "Sports & Outdoors",
            "Cameras & Drones",
            "Women's Bags",
            "Jewellery & Accessories",
            "Men's Wear",
            "Home & Living",
            "Beauty & Personal Care",
            "Health & Wellness",
            "Toys, Kids & Babies",
            "Video Games",
            "Hobbies & Books",
            "Pet Supplies",
            "Men's Bags",
            "Watches",
            "Women's Shoes",
            "Automotive",
            "Dining, Travel & Services",
            "Men's Shoes",
            "Travel & Luggage",
            "Miscellaneous",
        ]

        created_count = 0
        for category_name in categories:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))
            else:
                self.stdout.write(f'Category already exists: {category_name}')

        self.stdout.write(self.style.SUCCESS(f'\nTotal categories created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total categories in database: {Category.objects.count()}'))
