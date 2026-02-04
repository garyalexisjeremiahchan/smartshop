# SmartShop - E-Commerce Platform

SmartShop is a comprehensive e-commerce platform built with Django, Bootstrap, and MySQL. It provides a modern, responsive interface for online shopping with features including product browsing, shopping cart, checkout, user authentication, and order management.

## Features

- **User Authentication**: Register, login, and manage user profiles
- **Product Catalog**: Browse products by categories with sorting and filtering
- **Product Details**: Detailed product pages with images, specifications, and reviews
- **Shopping Cart**: Add, update, and remove items from cart
- **Checkout**: Complete order placement with shipping information
- **Order Management**: View order history and order details
- **Product Reviews**: Rate and review products (authenticated users only)
- **Admin Interface**: Complete CRUD operations for products, categories, orders, and users
- **Responsive Design**: Mobile-friendly Bootstrap interface

## Technology Stack

- **Backend**: Python 3.13, Django 6.0
- **Frontend**: Bootstrap 5, JavaScript, HTML5, CSS3
- **Database**: MySQL
- **Email**: Django SMTP Email Backend
- **Image Handling**: Pillow
- **Forms**: django-crispy-forms with Bootstrap 5
- **API Integration**: OpenAI (for future AI features)

## Installation

### Prerequisites

- Python 3.13
- MySQL Server
- Virtual Environment

### Setup Instructions

1. **Clone the repository** (or navigate to the project directory)

2. **Activate the virtual environment**:
   ```bash
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL Database**:
   - Create a MySQL database named `smartshop_db`
   - Update database credentials in `smartshop/settings.py`:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': 'smartshop_db',
             'USER': 'root',
             'PASSWORD': 'your_password',  # Update with your MySQL password
             'HOST': 'localhost',
             'PORT': '3306',
         }
     }
     ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate categories**:
   ```bash
   python manage.py populate_categories
   ```

8. **Add the SmartShop logo**:
   - Save the logo image as `static/images/logo.png`

9. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

10. **Access the application**:
    - Website: http://127.0.0.1:8000/
    - Admin Panel: http://127.0.0.1:8000/admin/

## Project Structure

```
gas-smartshop/
├── smartshop/              # Project configuration
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── store/                  # Store app (main e-commerce functionality)
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── forms.py           # Form definitions
│   ├── urls.py            # Store URL patterns
│   ├── admin.py           # Admin configuration
│   └── context_processors.py  # Custom context processors
├── accounts/               # User authentication app
│   ├── models.py          # User models (if extended)
│   ├── views.py           # Authentication views
│   ├── forms.py           # Authentication forms
│   └── urls.py            # Account URL patterns
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── store/             # Store templates
│   └── accounts/          # Account templates
├── static/                 # Static files
│   ├── css/               # CSS files
│   ├── js/                # JavaScript files
│   └── images/            # Images and icons
├── media/                  # User-uploaded files
│   ├── products/          # Product images
│   └── categories/        # Category icons
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Database Models

### Category
- Product categories with icons and descriptions

### Product
- Product information including price, stock, specifications
- Supports multiple images per product
- Automatic slug generation
- Average rating calculation

### ProductImage
- Multiple images per product
- Primary image designation

### Review
- Product reviews with ratings (1-5 stars)
- One review per user per product

### Cart
- Shopping cart for authenticated and guest users
- Session-based for guest users

### CartItem
- Individual cart items with quantity

### Order
- Customer orders with shipping information
- Unique order number generation
- Order status tracking

### OrderItem
- Items within an order
- Stores product details at time of order

## Usage

### Admin Panel

1. Login to admin panel at `/admin/`
2. Add products with images, pricing, and specifications
3. Manage categories and organize products
4. View and manage orders
5. Monitor and approve product reviews

### Customer Features

1. **Browse Products**: Navigate categories or search for products
2. **Product Details**: View detailed product information and reviews
3. **Add to Cart**: Select products and add to shopping cart
4. **Checkout**: Complete purchase with shipping information
5. **Order History**: View past orders and order details
6. **Reviews**: Rate and review purchased products

## Configuration

### Email Settings (Optional)

Update in `smartshop/settings.py`:
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### OpenAI API (For future AI features)

Update in `smartshop/settings.py`:
```python
OPENAI_API_KEY = 'your-openai-api-key'
```

## Future Enhancements

- Payment gateway integration
- Order tracking and shipping status
- Wishlist functionality
- Product recommendations using AI
- Email notifications
- Advanced search with filters
- Product comparison
- Customer support chat

## License

This project is for educational purposes.

## Support

For issues or questions, please contact the development team.
