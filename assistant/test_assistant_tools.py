"""
Unit Tests for Virtual Shopping Assistant Tools

This module contains comprehensive unit tests for the assistant tools:
- search_products
- get_product_details
- get_product_specs
- get_availability
- get_reviews_summary
- get_similar_products
- get_categories
- get_top_selling_products
- add_to_cart

Test Categories:
1. Search Products Tests
2. Product Details Tests  
3. Product Specifications Tests
4. Availability Tests
5. Reviews Summary Tests
6. Similar Products Tests
7. Categories Tests
8. Top Selling Products Tests
9. Add to Cart Tests

Running Tests:
    python manage.py test assistant.test_assistant_tools -v 2
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from store.models import Product, Category, Review, Cart, CartItem
from assistant.tools import (
    search_products, get_product_details, get_product_specs,
    get_availability, get_reviews_summary, get_similar_products,
    get_categories, get_top_selling_products, add_to_cart
)
from decimal import Decimal


class SearchProductsToolTests(TestCase):
    """
    Test Case: search_products Tool
    
    Tests the search_products function with various parameters
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        # Create test products
        self.laptop = Product.objects.create(
            category=self.category,
            name='Gaming Laptop',
            slug='gaming-laptop',
            description='High performance gaming laptop',
            specifications='16GB RAM, 512GB SSD',
            price=Decimal('999.99'),
            stock=10,
            units_sold=50,
            is_active=True
        )
        
        self.mouse = Product.objects.create(
            category=self.category,
            name='Wireless Mouse',
            slug='wireless-mouse',
            description='Ergonomic wireless mouse',
            price=Decimal('29.99'),
            stock=100,
            units_sold=200,
            is_active=True
        )
    
    def test_search_products_by_query(self):
        """Test searching products by keyword"""
        result = search_products(query='laptop')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['products']), 1)
        self.assertEqual(result['products'][0]['title'], 'Gaming Laptop')
    
    def test_search_products_by_category(self):
        """Test searching products by category"""
        result = search_products(category='electronics')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['products']), 2)
    
    def test_search_products_with_price_filter(self):
        """Test searching with price range"""
        result = search_products(min_price=500, max_price=1500)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['products']), 1)
        self.assertEqual(result['products'][0]['title'], 'Gaming Laptop')
    
    def test_search_products_sort_by_price_low_high(self):
        """Test sorting by price ascending"""
        result = search_products(sort='price_low_high', limit=10)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['products'][0]['title'], 'Wireless Mouse')
        self.assertEqual(result['products'][1]['title'], 'Gaming Laptop')
    
    def test_search_products_sort_by_popularity(self):
        """Test sorting by popularity (units sold)"""
        result = search_products(sort='popular', limit=10)
        
        self.assertTrue(result['success'])
        # Mouse sold 200, Laptop sold 50
        self.assertEqual(result['products'][0]['title'], 'Wireless Mouse')
    
    def test_search_products_limit_results(self):
        """Test limiting number of results"""
        # Create more products
        for i in range(15):
            Product.objects.create(
                category=self.category,
                name=f'Product {i}',
                slug=f'product-{i}',
                description='Test product',
                price=Decimal('10.00'),
                stock=5,
                is_active=True
            )
        
        result = search_products(limit=5)
        self.assertTrue(result['success'])
        self.assertLessEqual(len(result['products']), 5)
    
    def test_search_products_in_stock_only(self):
        """Test filtering for in-stock products only"""
        # Create out of stock product
        Product.objects.create(
            category=self.category,
            name='Out of Stock Item',
            slug='out-of-stock',
            description='Test',
            price=Decimal('50.00'),
            stock=0,
            is_active=True
        )
        
        result = search_products(in_stock_only=True)
        
        self.assertTrue(result['success'])
        for product in result['products']:
            self.assertGreater(product['stock_quantity'], 0)
    
    def test_search_products_returns_correct_structure(self):
        """Test that search results have correct structure"""
        result = search_products(query='laptop')
        
        self.assertTrue(result['success'])
        self.assertIn('products', result)
        
        product = result['products'][0]
        self.assertIn('id', product)
        self.assertIn('title', product)
        self.assertIn('price', product)
        self.assertIn('currency', product)
        self.assertIn('stock_status', product)
        self.assertIn('url', product)
        self.assertIn('category', product)
    
    def test_search_products_no_results(self):
        """Test search with no matching products"""
        result = search_products(query='nonexistent-product-xyz')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['products']), 0)


class GetProductDetailsToolTests(TestCase):
    """
    Test Case: get_product_details Tool
    
    Tests retrieving detailed product information
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            slug='test-laptop',
            description='Detailed laptop description',
            specifications='CPU: Intel i7\nRAM: 16GB',
            price=Decimal('1299.99'),
            stock=5,
            units_sold=25,
            is_active=True
        )
        
        # Add a review
        user = User.objects.create_user(
            username='reviewer',
            password='pass123'
        )
        Review.objects.create(
            product=self.product,
            user=user,
            rating=5,
            comment='Excellent laptop!',
            is_approved=True
        )
    
    def test_get_product_details_success(self):
        """Test getting product details successfully"""
        result = get_product_details(self.product.id)
        
        self.assertTrue(result['success'])
        self.assertIn('product', result)
        self.assertEqual(result['product']['title'], 'Test Laptop')
        self.assertEqual(result['product']['price'], float(self.product.price))
    
    def test_get_product_details_includes_specifications(self):
        """Test that product details include basic description"""
        result = get_product_details(self.product.id)
        
        self.assertTrue(result['success'])
        self.assertIn('description', result['product'])
        self.assertEqual(result['product']['description'], 'Detailed laptop description')
    
    def test_get_product_details_includes_rating(self):
        """Test that product details include rating"""
        result = get_product_details(self.product.id)
        
        self.assertTrue(result['success'])
        self.assertIn('rating', result['product'])
        self.assertGreater(result['product']['rating'], 0)
    
    def test_get_product_details_nonexistent_product(self):
        """Test getting details for non-existent product"""
        result = get_product_details(99999)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_get_product_details_inactive_product(self):
        """Test getting details for inactive product"""
        inactive = Product.objects.create(
            category=self.category,
            name='Inactive Product',
            slug='inactive',
            description='Test',
            price=Decimal('50.00'),
            stock=5,
            is_active=False
        )
        
        result = get_product_details(inactive.id)
        
        self.assertFalse(result['success'])


class GetAvailabilityToolTests(TestCase):
    """
    Test Case: get_availability Tool
    
    Tests checking product availability
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.in_stock = Product.objects.create(
            category=self.category,
            name='In Stock Product',
            slug='in-stock',
            description='Test',
            price=Decimal('100.00'),
            stock=50,
            is_active=True
        )
        
        self.low_stock = Product.objects.create(
            category=self.category,
            name='Low Stock Product',
            slug='low-stock',
            description='Test',
            price=Decimal('100.00'),
            stock=3,
            is_active=True
        )
        
        self.out_of_stock = Product.objects.create(
            category=self.category,
            name='Out of Stock Product',
            slug='out-of-stock',
            description='Test',
            price=Decimal('100.00'),
            stock=0,
            is_active=True
        )
    
    def test_availability_in_stock(self):
        """Test availability for well-stocked product"""
        result = get_availability(self.in_stock.id)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['is_available'])
        self.assertEqual(result['status'], 'in_stock')
        self.assertEqual(result['stock_quantity'], 50)
    
    def test_availability_low_stock(self):
        """Test availability for low stock product"""
        result = get_availability(self.low_stock.id)
        
        self.assertTrue(result['success'])
        self.assertTrue(result['is_available'])
        self.assertEqual(result['status'], 'low_stock')
    
    def test_availability_out_of_stock(self):
        """Test availability for out of stock product"""
        result = get_availability(self.out_of_stock.id)
        
        self.assertTrue(result['success'])
        self.assertFalse(result['is_available'])
        self.assertEqual(result['status'], 'out_of_stock')
        self.assertEqual(result['stock_quantity'], 0)
    
    def test_availability_nonexistent_product(self):
        """Test availability for non-existent product"""
        result = get_availability(99999)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class GetCategoriesToolTests(TestCase):
    """
    Test Case: get_categories Tool
    
    Tests retrieving product categories
    """
    
    def setUp(self):
        """Set up test data"""
        Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        Category.objects.create(
            name='Clothing',
            slug='clothing',
            is_active=True
        )
        Category.objects.create(
            name='Inactive Category',
            slug='inactive',
            is_active=False
        )
    
    def test_get_categories_returns_active_only(self):
        """Test that only active categories are returned"""
        result = get_categories()
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['categories']), 2)
    
    def test_get_categories_structure(self):
        """Test that categories have correct structure"""
        result = get_categories()
        
        self.assertTrue(result['success'])
        category = result['categories'][0]
        self.assertIn('name', category)
        self.assertIn('slug', category)
        self.assertIn('url', category)


class AddToCartToolTests(TestCase):
    """
    Test Case: add_to_cart Tool
    
    Tests adding products to shopping cart
    """
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            description='Test',
            price=Decimal('99.99'),
            stock=10,
            is_active=True
        )
    
    def test_add_to_cart_requires_request(self):
        """Test that add_to_cart requires request object"""
        result = add_to_cart(self.product.id, quantity=1, request=None)
        
        self.assertFalse(result['success'])
        self.assertIn('Request context required', result['error'])
    
    def test_add_to_cart_authenticated_user(self):
        """Test adding to cart for authenticated user"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        result = add_to_cart(self.product.id, quantity=1, request=request)
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.assertIn('cart', result)
    
    def test_add_to_cart_invalid_product(self):
        """Test adding non-existent product to cart"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        result = add_to_cart(99999, quantity=1, request=request)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_add_to_cart_quantity_validation(self):
        """Test quantity validation"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        # Try to add more than available stock
        result = add_to_cart(self.product.id, quantity=100, request=request)
        
        self.assertFalse(result['success'])
        self.assertIn('available in stock', result['error'])
    
    def test_add_to_cart_updates_existing_item(self):
        """Test that adding existing product updates quantity"""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        # Add product first time
        result1 = add_to_cart(self.product.id, quantity=1, request=request)
        self.assertTrue(result1['success'])
        
        # Add same product again
        result2 = add_to_cart(self.product.id, quantity=2, request=request)
        self.assertTrue(result2['success'])
        
        # Find cart and check quantity
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 3)


class GetTopSellingProductsToolTests(TestCase):
    """
    Test Case: get_top_selling_products Tool
    
    Tests retrieving top selling products
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        # Create products with different sales
        self.bestseller = Product.objects.create(
            category=self.category,
            name='Bestseller',
            slug='bestseller',
            description='Top selling product',
            price=Decimal('50.00'),
            stock=10,
            units_sold=1000,
            is_active=True
        )
        
        self.moderate = Product.objects.create(
            category=self.category,
            name='Moderate Seller',
            slug='moderate',
            description='Moderate sales',
            price=Decimal('50.00'),
            stock=10,
            units_sold=100,
            is_active=True
        )
        
        self.new_product = Product.objects.create(
            category=self.category,
            name='New Product',
            slug='new-product',
            description='Just launched',
            price=Decimal('50.00'),
            stock=10,
            units_sold=5,
            is_active=True
        )
    
    def test_get_top_selling_products_returns_sorted_list(self):
        """Test that top selling products are sorted by units sold"""
        result = get_top_selling_products(limit=10)
        
        self.assertTrue(result['success'])
        self.assertGreaterEqual(len(result['products']), 3)
        
        # First product should be bestseller
        self.assertEqual(result['products'][0]['title'], 'Bestseller')
    
    def test_get_top_selling_products_respects_limit(self):
        """Test that limit parameter is respected"""
        result = get_top_selling_products(limit=2)
        
        self.assertTrue(result['success'])
        self.assertLessEqual(len(result['products']), 2)
