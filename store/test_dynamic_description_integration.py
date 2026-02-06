"""
Integration Tests for Dynamic Product Description Feature

This module contains integration tests that verify the complete workflow
of the dynamic product description feature, including view integration,
template rendering, and end-to-end user scenarios.

Test Categories:
1. View Integration Tests
2. Template Rendering Tests
3. End-to-End Workflow Tests
4. Database Persistence Tests
5. Performance Tests

Running Tests:
    python manage.py test store.test_dynamic_description_integration -v 2
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from store.models import Product, Category, Review
from store.dynamic_description import DynamicDescriptionGenerator
import logging

# Disable logging during tests
logging.disable(logging.CRITICAL)


class ProductDetailViewIntegrationTests(TestCase):
    """
    Test Case: Product Detail View Integration
    
    Tests the integration of dynamic description generation within
    the product detail view.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        # Create test product
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            description='Original description for testing',
            specifications='Feature 1\nFeature 2\nFeature 3',
            price=49.99,
            stock=10,
            is_active=True
        )
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_view_generates_description_on_first_visit(self, mock_generate):
        """Test that description is generated on first product view"""
        mock_generate.return_value = "AI generated description"
        
        # Visit product detail page
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Verify description was generated
        self.product.refresh_from_db()
        self.assertEqual(self.product.dynamic_description, "AI generated description")
        self.assertIsNotNone(self.product.dynamic_description_generated_at)
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_view_does_not_regenerate_fresh_description(self, mock_generate):
        """Test that fresh description is not regenerated on subsequent visits"""
        # Set fresh description with proper timestamp management
        generation_time = timezone.now() - timedelta(days=1)
        self.product.dynamic_description = "Existing description"
        self.product.dynamic_description_generated_at = generation_time
        self.product.save(update_fields=['dynamic_description', 'dynamic_description_generated_at'])
        
        # Ensure product updated_at is before generation time
        Product.objects.filter(id=self.product.id).update(
            updated_at=generation_time - timedelta(hours=1)
        )
        
        mock_generate.return_value = "New description"
        
        # Visit product detail page
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Verify description was NOT regenerated
        self.product.refresh_from_db()
        self.assertEqual(self.product.dynamic_description, "Existing description")
        mock_generate.assert_not_called()
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_view_regenerates_old_description(self, mock_generate):
        """Test that old description (>7 days) is regenerated"""
        # Set old description
        self.product.dynamic_description = "Old description"
        self.product.dynamic_description_generated_at = timezone.now() - timedelta(days=10)
        self.product.save()
        
        mock_generate.return_value = "New fresh description"
        
        # Visit product detail page
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Verify description was regenerated
        self.product.refresh_from_db()
        self.assertEqual(self.product.dynamic_description, "New fresh description")
        mock_generate.assert_called_once()
    
    def test_view_handles_generation_failure_gracefully(self):
        """Test that view continues to work even if description generation fails"""
        # Ensure no description exists
        self.product.dynamic_description = ""
        self.product.save()
        
        # Visit product detail page (will try to generate but might fail without API key)
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Page should still load successfully
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)


class TemplateDynamicDescriptionRenderingTests(TestCase):
    """
    Test Case: Template Rendering
    
    Tests the correct rendering of dynamic descriptions in the
    product detail template.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Smart Speaker',
            slug='smart-speaker',
            description='Voice-activated speaker',
            price=99.99,
            stock=15,
            is_active=True
        )
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_template_displays_dynamic_description_when_present(self, mock_generate):
        """Test that template displays dynamic description when it exists"""
        # Set dynamic description and prevent regeneration
        generation_time = timezone.now()
        self.product.dynamic_description = "Experience crystal-clear sound with our smart speaker"
        self.product.dynamic_description_generated_at = generation_time
        self.product.save(update_fields=['dynamic_description', 'dynamic_description_generated_at'])
        
        # Ensure product updated_at is before generation time
        Product.objects.filter(id=self.product.id).update(
            updated_at=generation_time - timedelta(hours=1)
        )
        
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Check that dynamic description is displayed
        self.assertContains(response, "Experience crystal-clear sound")
        self.assertContains(response, "AI-Enhanced Description")
    
    def test_template_displays_original_description_when_no_dynamic(self):
        """Test that template displays original description when no dynamic description exists"""
        # Ensure no dynamic description
        self.product.dynamic_description = ""
        self.product.save()
        
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Should display original description
        self.assertContains(response, self.product.description)
    
    def test_template_shows_technical_details_accordion(self):
        """Test that template includes technical details accordion when dynamic description exists"""
        self.product.dynamic_description = "Great product description"
        self.product.dynamic_description_generated_at = timezone.now()
        self.product.save()
        
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Check for accordion elements
        self.assertContains(response, "Technical Details")
        self.assertContains(response, "accordion")
    
    def test_template_includes_ai_indicator_icon(self):
        """Test that template includes AI indicator when dynamic description is shown"""
        self.product.dynamic_description = "AI-powered description"
        self.product.dynamic_description_generated_at = timezone.now()
        self.product.save()
        
        url = reverse('store:product_detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        # Check for AI magic icon
        self.assertContains(response, "bi-magic")


class EndToEndDynamicDescriptionWorkflowTests(TestCase):
    """
    Test Case: End-to-End Workflow
    
    Tests complete user workflows involving dynamic product descriptions,
    from product creation through viewing and updating.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123'
        )
        
        self.category = Category.objects.create(
            name='Fashion',
            slug='fashion',
            is_active=True
        )
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_complete_product_lifecycle_workflow(self, mock_generate):
        """Test complete workflow: create product -> view -> review -> regenerate"""
        mock_generate.return_value = "Initial dynamic description"
        
        # Step 1: Create product
        product = Product.objects.create(
            category=self.category,
            name='Designer Dress',
            slug='designer-dress',
            description='Elegant evening dress',
            price=199.99,
            stock=5,
            is_active=True
        )
        
        # Step 2: First view generates description
        url = reverse('store:product_detail', kwargs={'slug': product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        product.refresh_from_db()
        self.assertEqual(product.dynamic_description, "Initial dynamic description")
        first_generation_time = product.dynamic_description_generated_at
        
        # Step 3: Add a review
        self.client.login(username='customer', password='password123')
        review_data = {
            'rating': 5,
            'title': 'Beautiful dress',
            'comment': 'Perfect fit and gorgeous design'
        }
        self.client.post(url, review_data)
        
        # Step 4: Update description to include new review feedback
        mock_generate.return_value = "Updated description mentioning perfect fit"
        
        # Simulate time passing (8 days)
        product.dynamic_description_generated_at = timezone.now() - timedelta(days=8)
        product.save()
        
        # Visit again to trigger regeneration
        response = self.client.get(url)
        
        product.refresh_from_db()
        self.assertEqual(product.dynamic_description, "Updated description mentioning perfect fit")
        self.assertGreater(product.dynamic_description_generated_at, first_generation_time)
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_product_update_triggers_regeneration(self, mock_generate):
        """Test that updating product details triggers description regeneration"""
        mock_generate.return_value = "First description"
        
        # Create and view product
        product = Product.objects.create(
            category=self.category,
            name='Handbag',
            slug='handbag',
            description='Leather handbag',
            price=149.99,
            stock=10,
            is_active=True
        )
        
        url = reverse('store:product_detail', kwargs={'slug': product.slug})
        self.client.get(url)
        
        # Update product
        product.price = 129.99
        product.description = 'Premium leather handbag with gold hardware'
        product.save()
        
        # Mock new description
        mock_generate.return_value = "Updated description with new details"
        
        # View again
        self.client.get(url)
        
        product.refresh_from_db()
        # Should have new description because product was updated
        self.assertEqual(product.dynamic_description, "Updated description with new details")


class DatabasePersistenceDynamicDescriptionTests(TestCase):
    """
    Test Case: Database Persistence
    
    Tests that dynamic descriptions are correctly persisted to
    the database and can be retrieved reliably.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.category = Category.objects.create(
            name='Books',
            slug='books'
        )
    
    def test_dynamic_description_persists_across_queries(self):
        """Test that dynamic description persists when querying database"""
        product = Product.objects.create(
            category=self.category,
            name='Python Book',
            slug='python-book',
            description='Learn Python',
            price=39.99,
            stock=100,
            dynamic_description='Comprehensive guide to Python programming',
            dynamic_description_generated_at=timezone.now()
        )
        
        # Query product from database
        retrieved_product = Product.objects.get(id=product.id)
        
        self.assertEqual(
            retrieved_product.dynamic_description,
            'Comprehensive guide to Python programming'
        )
        self.assertIsNotNone(retrieved_product.dynamic_description_generated_at)
    
    def test_dynamic_description_survives_product_updates(self):
        """Test that dynamic description is preserved when updating other fields"""
        product = Product.objects.create(
            category=self.category,
            name='Novel',
            slug='novel',
            description='Fiction book',
            price=24.99,
            stock=50,
            dynamic_description='Captivating story that keeps you engaged',
            dynamic_description_generated_at=timezone.now()
        )
        
        original_description = product.dynamic_description
        original_timestamp = product.dynamic_description_generated_at
        
        # Update price (not dynamic description)
        product.price = 19.99
        product.save()
        
        product.refresh_from_db()
        self.assertEqual(product.dynamic_description, original_description)
        self.assertEqual(product.dynamic_description_generated_at, original_timestamp)
    
    def test_can_query_products_with_dynamic_descriptions(self):
        """Test querying products that have dynamic descriptions"""
        # Create products with and without dynamic descriptions
        product1 = Product.objects.create(
            category=self.category,
            name='Book 1',
            slug='book-1',
            description='Description 1',
            price=29.99,
            stock=10,
            dynamic_description='Dynamic 1',
            dynamic_description_generated_at=timezone.now()
        )
        
        product2 = Product.objects.create(
            category=self.category,
            name='Book 2',
            slug='book-2',
            description='Description 2',
            price=34.99,
            stock=15
        )
        
        # Query products with dynamic descriptions
        products_with_dynamic = Product.objects.exclude(
            dynamic_description=''
        ).exclude(
            dynamic_description__isnull=True
        )
        
        self.assertEqual(products_with_dynamic.count(), 1)
        self.assertEqual(products_with_dynamic.first().id, product1.id)
    
    def test_can_query_products_needing_regeneration(self):
        """Test querying products that need description regeneration"""
        # Create product with old description
        old_product = Product.objects.create(
            category=self.category,
            name='Old Book',
            slug='old-book',
            description='Needs update',
            price=19.99,
            stock=5,
            dynamic_description='Old description',
            dynamic_description_generated_at=timezone.now() - timedelta(days=10)
        )
        
        # Create product with fresh description
        fresh_product = Product.objects.create(
            category=self.category,
            name='Fresh Book',
            slug='fresh-book',
            description='Recent',
            price=24.99,
            stock=8,
            dynamic_description='Fresh description',
            dynamic_description_generated_at=timezone.now() - timedelta(days=2)
        )
        
        # Query products with old descriptions
        cutoff_date = timezone.now() - timedelta(days=7)
        old_products = Product.objects.filter(
            dynamic_description_generated_at__lt=cutoff_date
        )
        
        self.assertEqual(old_products.count(), 1)
        self.assertEqual(old_products.first().id, old_product.id)


class DynamicDescriptionWithReviewsIntegrationTests(TestCase):
    """
    Test Case: Integration with Reviews
    
    Tests how dynamic descriptions interact with the review system,
    including incorporating review feedback into descriptions.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        self.user1 = User.objects.create_user(
            username='reviewer1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='reviewer2',
            password='pass123'
        )
        
        self.category = Category.objects.create(
            name='Gadgets',
            slug='gadgets'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Wireless Earbuds',
            slug='wireless-earbuds',
            description='Bluetooth earbuds',
            price=79.99,
            stock=25
        )
    
    def test_prompt_includes_recent_reviews(self):
        """Test that prompt includes recent customer reviews"""
        # Add reviews
        Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            title='Excellent sound',
            comment='Amazing bass and clarity',
            is_approved=True
        )
        
        Review.objects.create(
            product=self.product,
            user=self.user2,
            rating=4,
            title='Good battery life',
            comment='Lasts all day on a single charge',
            is_approved=True
        )
        
        prompt = self.generator._build_prompt(self.product)
        
        # Verify reviews are in prompt
        self.assertIn('Amazing bass and clarity', prompt)
        self.assertIn('Lasts all day', prompt)
    
    def test_description_generation_with_review_context(self):
        """Test that descriptions can leverage review insights"""
        # Add a positive review mentioning comfort
        Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            title='Very comfortable',
            comment='So comfortable I forget I am wearing them',
            is_approved=True
        )
        
        prompt = self.generator._build_prompt(self.product)
        
        # Prompt should include this comfort feedback
        self.assertIn('comfortable', prompt.lower())


class DynamicDescriptionPerformanceTests(TestCase):
    """
    Test Case: Performance
    
    Tests performance characteristics of the dynamic description feature,
    including generation time and database query efficiency.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.category = Category.objects.create(
            name='Performance Test',
            slug='performance-test'
        )
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_batch_update_performance(self, mock_generate):
        """Test performance of updating multiple products"""
        mock_generate.return_value = "Test description"
        
        # Create 10 products
        products = []
        for i in range(10):
            product = Product.objects.create(
                category=self.category,
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Description {i}',
                price=10.00 + i,
                stock=10
            )
            products.append(product)
        
        # Update all products
        generator = DynamicDescriptionGenerator()
        
        import time
        start_time = time.time()
        
        for product in products:
            generator.update_product_description(product)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete in reasonable time (< 5 seconds for mocked calls)
        self.assertLess(elapsed, 5.0)
        
        # Verify all were updated
        updated_count = Product.objects.exclude(
            dynamic_description=''
        ).count()
        self.assertEqual(updated_count, 10)
    
    def test_database_query_efficiency(self):
        """Test that retrieving products with descriptions is efficient"""
        # Create products with descriptions
        for i in range(20):
            Product.objects.create(
                category=self.category,
                name=f'Efficient Product {i}',
                slug=f'efficient-product-{i}',
                description=f'Description {i}',
                price=15.00,
                stock=5,
                dynamic_description=f'Dynamic {i}',
                dynamic_description_generated_at=timezone.now()
            )
        
        # Query with select_related to minimize queries
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as context:
            products = list(Product.objects.filter(
                category=self.category
            ).select_related('category'))
            
            # Access dynamic descriptions
            for product in products:
                _ = product.dynamic_description
        
        # Should be efficient (< 5 queries for 20 products)
        self.assertLess(len(context.captured_queries), 5)


# Re-enable logging
logging.disable(logging.NOTSET)
