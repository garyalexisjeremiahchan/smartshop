"""
Sample Data Creation Guide for SmartShop
=========================================

This guide helps you add sample products to test the SmartShop application.

OPTION 1: Via Django Admin Panel (Recommended for testing)
-----------------------------------------------------------

1. Start the server: python manage.py runserver
2. Go to http://127.0.0.1:8000/admin/
3. Login with superuser credentials
4. Click on "Products" → "Add Product"

For each product, enter:
- Category: Select from dropdown
- Name: Product name
- Description: Detailed description
- Specifications: Technical details (optional)
- Price: Product price (e.g., 29.99)
- Stock: Available quantity (e.g., 100)
- Units sold: Initial sales count (e.g., 0)
- Is active: Check to make visible

5. After saving, add product images:
   - Scroll to "Product images" section at bottom
   - Click "Add another Product image"
   - Upload image and check "Is primary" for main image
   - Add multiple images if desired

6. Repeat for multiple products


SAMPLE PRODUCT IDEAS BY CATEGORY
---------------------------------

Women's Apparel:
- Summer Floral Dress - $49.99
- Cotton Casual Top - $24.99
- Denim Jeans - $59.99

Mobile & Gadgets:
- Smartphone X Pro - $899.99
- Wireless Earbuds - $79.99
- Phone Case Set - $19.99

Computers & Peripherals:
- Gaming Laptop 15" - $1299.99
- Wireless Mouse - $29.99
- Mechanical Keyboard - $89.99

Home Appliances:
- Air Fryer 5L - $129.99
- Coffee Maker - $79.99
- Vacuum Cleaner - $199.99

Beauty & Personal Care:
- Skincare Set - $45.99
- Hair Dryer Professional - $69.99
- Makeup Palette - $34.99


OPTION 2: Via Django Shell (Bulk Creation)
-------------------------------------------

Run: python manage.py shell

Then execute:

```python
from store.models import Category, Product, ProductImage
from django.core.files import File

# Get a category
category = Category.objects.get(name="Mobile & Gadgets")

# Create a product
product = Product.objects.create(
    category=category,
    name="Smartphone X Pro",
    description="Latest flagship smartphone with advanced features",
    specifications="6.7 inch display, 128GB storage, 5G enabled",
    price=899.99,
    stock=50,
    units_sold=15,
    is_active=True
)

# Add product image (if you have image file)
# with open('path/to/image.jpg', 'rb') as f:
#     ProductImage.objects.create(
#         product=product,
#         image=File(f),
#         is_primary=True
#     )

print(f"Created product: {product.name}")
```


ADDING REVIEWS
--------------

Reviews require authenticated users:

1. Create a regular user account (not superuser)
2. Login to the website
3. Browse to a product page
4. Scroll to reviews section
5. Submit a review with rating (1-5 stars)

Or via Django shell:

```python
from django.contrib.auth.models import User
from store.models import Product, Review

user = User.objects.first()  # or get specific user
product = Product.objects.first()  # or get specific product

Review.objects.create(
    product=product,
    user=user,
    rating=5,
    title="Excellent product!",
    comment="Very satisfied with this purchase. Highly recommended!",
    is_approved=True
)
```


TIPS FOR PRODUCT IMAGES
------------------------

1. Image sizes: 800x800px recommended
2. Format: JPG or PNG
3. File size: Keep under 1MB for faster loading
4. Use placeholder images: https://via.placeholder.com/800x800
5. Free stock photos: unsplash.com, pexels.com

Example using placeholder in admin:
- Copy URL: https://via.placeholder.com/800x800/FF6B35/FFFFFF?text=Product
- Use browser to save image
- Upload to product


TESTING WORKFLOW
----------------

After adding products:

1. Browse home page - view featured products
2. Click category - see filtered products
3. Try sorting options (Popular, Latest, Price)
4. View product detail page
5. Add to cart
6. Update quantities in cart
7. Proceed to checkout
8. Complete order
9. View order in order history
10. Leave a product review


BULK IMPORT (Advanced)
----------------------

For importing many products, create a CSV file and use Django management command:

Create: store/management/commands/import_products.py

```python
import csv
from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open('products.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = Category.objects.get(name=row['category'])
                Product.objects.create(
                    category=category,
                    name=row['name'],
                    description=row['description'],
                    price=row['price'],
                    stock=row['stock']
                )
```

Run: python manage.py import_products
"""

if __name__ == "__main__":
    print(__doc__)
