"""
SmartShop Setup Instructions
=============================

Follow these steps to set up and run SmartShop:

STEP 1: Create MySQL Database
------------------------------
Open MySQL command line or MySQL Workbench and run:
    CREATE DATABASE IF NOT EXISTS smartshop_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Or use the provided SQL file:
    mysql -u root -p < create_database.sql


STEP 2: Configure Database Settings
------------------------------------
Edit smartshop/settings.py and update the DATABASES configuration with your MySQL password:
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'smartshop_db',
            'USER': 'root',
            'PASSWORD': 'YOUR_MYSQL_PASSWORD',  # ← Update this
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }


STEP 3: Run Migrations
----------------------
Execute these commands in order:
    python manage.py migrate


STEP 4: Create Superuser
-------------------------
Create an admin account:
    python manage.py createsuperuser

Follow the prompts to set username, email, and password.


STEP 5: Load Initial Data
--------------------------
Populate the database with categories:
    python manage.py populate_categories


STEP 6: Add Logo Image
-----------------------
Save the SmartShop logo image to:
    static/images/logo.png

The logo should be approximately 200x50 pixels (or similar aspect ratio).


STEP 7: Configure Email (Optional)
-----------------------------------
Edit smartshop/settings.py and update email settings:
    
    EMAIL_HOST_USER = 'your-email@gmail.com'
    EMAIL_HOST_PASSWORD = 'your-app-password'


STEP 8: Run Development Server
-------------------------------
Start the Django development server:
    python manage.py runserver

Access the site at: http://127.0.0.1:8000/
Access admin panel at: http://127.0.0.1:8000/admin/


STEP 9: Add Products via Admin
-------------------------------
1. Login to admin panel
2. Go to "Products" section
3. Click "Add Product"
4. Fill in product details:
   - Select category
   - Enter name, price, stock
   - Add description and specifications
   - Save the product
5. Add product images:
   - In the product detail page, scroll to "Product images"
   - Click "Add another Product image"
   - Upload image and mark as primary if it's the main image
   - Save


ADDITIONAL FEATURES
===================

Category Icons:
--------------
Add category icons via admin panel:
1. Go to Categories
2. Edit a category
3. Upload an icon image (80x80px recommended)
4. Save

Testing the Site:
-----------------
1. Register a new user account
2. Browse products by category
3. Add products to cart
4. Proceed to checkout
5. View order history in profile


TROUBLESHOOTING
===============

MySQL Connection Error:
- Ensure MySQL is running
- Verify database credentials in settings.py
- Check that smartshop_db database exists

Import Errors:
- Ensure virtual environment is activated: .venv\Scripts\activate
- Install requirements: pip install -r requirements.txt

Static Files Not Loading:
- Run: python manage.py collectstatic
- Ensure DEBUG = True in settings.py for development

"""

if __name__ == "__main__":
    print(__doc__)
