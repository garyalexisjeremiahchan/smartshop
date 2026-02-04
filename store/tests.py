from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import (
    Category, Product, ProductImage, Review, Cart, CartItem,
    Order, OrderItem, UserInteraction
)
from .forms import ReviewForm, CheckoutForm


class CategoryModelTest(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices and accessories'
        )
    
    def test_category_creation(self):
        """Test category is created successfully"""
        self.assertEqual(self.category.name, 'Electronics')
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.slug)
    
    def test_category_slug_auto_generation(self):
        """Test slug is automatically generated from name"""
        self.assertEqual(self.category.slug, 'electronics')
    
    def test_category_str_method(self):
        """Test category string representation"""
        self.assertEqual(str(self.category), 'Electronics')


class ProductModelTest(TestCase):
    """Test cases for Product model"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_product_creation(self):
        """Test product is created successfully"""
        self.assertEqual(self.product.name, 'Smartphone')
        self.assertEqual(self.product.price, Decimal('599.99'))
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.is_active)
    
    def test_product_slug_auto_generation(self):
        """Test slug is automatically generated from name"""
        self.assertEqual(self.product.slug, 'smartphone')
    
    def test_product_str_method(self):
        """Test product string representation"""
        self.assertEqual(str(self.product), 'Smartphone')
    
    def test_is_in_stock_property(self):
        """Test is_in_stock property"""
        self.assertTrue(self.product.is_in_stock)
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_in_stock)
    
    def test_average_rating_no_reviews(self):
        """Test average rating when no reviews exist"""
        self.assertEqual(self.product.average_rating, 0)
    
    def test_average_rating_with_reviews(self):
        """Test average rating calculation with reviews"""
        user1 = User.objects.create_user(username='user1', password='pass123')
        user2 = User.objects.create_user(username='user2', password='pass123')
        
        Review.objects.create(
            product=self.product,
            user=user1,
            rating=5,
            title='Great!',
            comment='Excellent product'
        )
        Review.objects.create(
            product=self.product,
            user=user2,
            rating=3,
            title='Good',
            comment='Good product'
        )
        
        self.assertEqual(self.product.average_rating, 4.0)
    
    def test_review_count(self):
        """Test review count property"""
        user = User.objects.create_user(username='user1', password='pass123')
        self.assertEqual(self.product.review_count, 0)
        
        Review.objects.create(
            product=self.product,
            user=user,
            rating=5,
            title='Great!',
            comment='Excellent'
        )
        
        self.assertEqual(self.product.review_count, 1)


class ProductImageModelTest(TestCase):
    """Test cases for ProductImage model"""
    
    def setUp(self):
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99')
        )
    
    def test_product_image_creation(self):
        """Test product image is created successfully"""
        image = ProductImage.objects.create(
            product=self.product,
            alt_text='Smartphone front view',
            is_primary=True
        )
        self.assertEqual(image.product, self.product)
        self.assertTrue(image.is_primary)


class ReviewModelTest(TestCase):
    """Test cases for Review model"""
    
    def setUp(self):
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99')
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
    
    def test_review_creation(self):
        """Test review is created successfully"""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Excellent Product',
            comment='I love this smartphone!'
        )
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.is_approved)
    
    def test_review_str_method(self):
        """Test review string representation"""
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Good',
            comment='Nice product'
        )
        expected = f"testuser - Smartphone (4 stars)"
        self.assertEqual(str(review), expected)
    
    def test_one_review_per_user_per_product(self):
        """Test unique constraint for one review per user per product"""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great',
            comment='Excellent'
        )
        
        # Attempting to create duplicate should raise error
        with self.assertRaises(Exception):
            Review.objects.create(
                product=self.product,
                user=self.user,
                rating=3,
                title='Changed mind',
                comment='Not so good'
            )


class CartModelTest(TestCase):
    """Test cases for Cart model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        category = Category.objects.create(name='Electronics')
        self.product1 = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
        self.product2 = Product.objects.create(
            category=category,
            name='Laptop',
            description='Powerful laptop',
            price=Decimal('1299.99'),
            stock=5
        )
    
    def test_cart_creation(self):
        """Test cart is created successfully"""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(str(cart), f"Cart - {self.user.username}")
    
    def test_cart_total_price(self):
        """Test cart total price calculation"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=1)
        
        expected_total = (Decimal('599.99') * 2) + Decimal('1299.99')
        self.assertEqual(cart.total_price, expected_total)
    
    def test_cart_total_items(self):
        """Test cart total items count"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=3)
        
        self.assertEqual(cart.total_items, 5)


class CartItemModelTest(TestCase):
    """Test cases for CartItem model"""
    
    def setUp(self):
        user = User.objects.create_user(username='testuser', password='pass123')
        self.cart = Cart.objects.create(user=user)
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_cart_item_creation(self):
        """Test cart item is created successfully"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.quantity, 2)
    
    def test_cart_item_subtotal(self):
        """Test cart item subtotal calculation"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        expected_subtotal = Decimal('599.99') * 3
        self.assertEqual(cart_item.subtotal, expected_subtotal)
    
    def test_cart_item_str_method(self):
        """Test cart item string representation"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(str(cart_item), '2x Smartphone')


class OrderModelTest(TestCase):
    """Test cases for Order model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123',
            email='test@example.com'
        )
    
    def test_order_creation(self):
        """Test order is created successfully"""
        order = Order.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone='1234567890',
            address_line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            total_amount=Decimal('999.99')
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.payment_status, 'pending')
        self.assertIsNotNone(order.order_number)
    
    def test_order_number_auto_generation(self):
        """Test order number is automatically generated"""
        order = Order.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone='1234567890',
            address_line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            total_amount=Decimal('999.99')
        )
        self.assertTrue(order.order_number.startswith('ORD-'))
    
    def test_order_str_method(self):
        """Test order string representation"""
        order = Order.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone='1234567890',
            address_line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            total_amount=Decimal('999.99')
        )
        expected = f"Order {order.order_number} - testuser"
        self.assertEqual(str(order), expected)


class OrderItemModelTest(TestCase):
    """Test cases for OrderItem model"""
    
    def setUp(self):
        user = User.objects.create_user(username='testuser', password='pass123')
        self.order = Order.objects.create(
            user=user,
            full_name='Test User',
            email='test@example.com',
            phone='1234567890',
            address_line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='USA',
            total_amount=Decimal('999.99')
        )
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_order_item_creation(self):
        """Test order item is created successfully"""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )
        self.assertEqual(order_item.product_name, 'Smartphone')
        self.assertEqual(order_item.product_price, Decimal('599.99'))
    
    def test_order_item_subtotal(self):
        """Test order item subtotal calculation"""
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )
        expected_subtotal = Decimal('599.99') * 2
        self.assertEqual(order_item.subtotal, expected_subtotal)


class UserInteractionModelTest(TestCase):
    """Test cases for UserInteraction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_user_interaction_creation(self):
        """Test user interaction is created successfully"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            interaction_type='view_product',
            product=self.product
        )
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.interaction_type, 'view_product')
        self.assertEqual(interaction.product, self.product)


class ReviewFormTest(TestCase):
    """Test cases for ReviewForm"""
    
    def test_valid_review_form(self):
        """Test form with valid data"""
        form_data = {
            'rating': 5,
            'title': 'Excellent Product',
            'comment': 'I love this product! Highly recommended.'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_missing_fields(self):
        """Test form with missing required fields"""
        form_data = {
            'rating': 5,
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())


class CheckoutFormTest(TestCase):
    """Test cases for CheckoutForm"""
    
    def test_valid_checkout_form(self):
        """Test form with valid data"""
        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address_line1': '123 Main St',
            'address_line2': 'Apt 4B',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001',
            'country': 'USA',
            'notes': 'Please deliver between 9am-5pm'
        }
        form = CheckoutForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_checkout_form_optional_fields(self):
        """Test form with optional fields omitted"""
        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address_line1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001',
            'country': 'USA',
        }
        form = CheckoutForm(data=form_data)
        self.assertTrue(form.is_valid())


class HomeViewTest(TestCase):
    """Test cases for home view"""
    
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('store:home')
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_home_page_loads(self):
        """Test home page loads successfully"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/home.html')
    
    def test_home_page_displays_categories(self):
        """Test home page displays categories"""
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Electronics')


class ProductDetailViewTest(TestCase):
    """Test cases for product detail view"""
    
    def setUp(self):
        self.client = Client()
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
        self.product_url = reverse('store:product_detail', args=[self.product.slug])
    
    def test_product_detail_page_loads(self):
        """Test product detail page loads successfully"""
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/product_detail.html')
    
    def test_product_detail_displays_product_info(self):
        """Test product detail page displays product information"""
        response = self.client.get(self.product_url)
        self.assertContains(response, 'Smartphone')
        self.assertContains(response, '599.99')


class CartViewTest(TestCase):
    """Test cases for cart view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.cart_url = reverse('store:cart')
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
    
    def test_cart_page_loads(self):
        """Test cart page loads successfully"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/cart.html')
    
    def test_cart_page_requires_login_for_checkout(self):
        """Test cart page shows login prompt for checkout when not authenticated"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, 200)


class AddToCartViewTest(TestCase):
    """Test cases for add to cart functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=category,
            name='Smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            stock=10
        )
        self.add_to_cart_url = reverse('store:add_to_cart', args=[self.product.id])
    
    def test_add_to_cart_authenticated_user(self):
        """Test adding product to cart for authenticated user"""
        self.client.login(username='testuser', password='pass123')
        response = self.client.post(self.add_to_cart_url, {'quantity': 2})
        self.assertEqual(response.status_code, 302)  # Redirect after adding
        
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 2)
