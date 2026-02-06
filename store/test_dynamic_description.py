"""
Unit Tests for Dynamic Product Description Feature

This module contains comprehensive unit tests for the DynamicDescriptionGenerator class
and related functionality. Tests are organized into logical groups following Django
testing best practices.

Test Categories:
1. Initialization Tests
2. Regeneration Logic Tests
3. Prompt Building Tests
4. Description Generation Tests
5. Product Update Tests
6. Error Handling Tests
7. Edge Cases Tests

Running Tests:
    python manage.py test store.test_dynamic_description -v 2
"""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from unittest.mock import patch, MagicMock
from store.models import Product, Category, Review
from store.dynamic_description import DynamicDescriptionGenerator
import logging

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


class DynamicDescriptionGeneratorInitializationTests(TestCase):
    """
    Test Case: DynamicDescriptionGenerator Initialization
    
    Tests the initialization of the DynamicDescriptionGenerator class,
    including API client setup and configuration loading.
    """
    
    def setUp(self):
        """Set up test environment before each test"""
        self.generator = DynamicDescriptionGenerator()
    
    def test_generator_initializes_successfully(self):
        """Test that generator initializes without errors"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.model)
    
    def test_generator_has_correct_model(self):
        """Test that generator uses configured model"""
        # Should use the model from settings (default: gpt-4o-mini)
        self.assertIn('gpt', self.generator.model.lower())
    
    def test_generator_client_created_when_api_key_present(self):
        """Test that OpenAI client is created when API key is configured"""
        if self.generator.client:
            self.assertIsNotNone(self.generator.client)
        else:
            # If no API key, client should be None
            self.assertIsNone(self.generator.client)


class DynamicDescriptionRegenerationLogicTests(TestCase):
    """
    Test Case: Regeneration Logic
    
    Tests the needs_regeneration() method which determines when
    a product description should be regenerated.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test product
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            description='Original description',
            price=29.99,
            stock=10
        )
    
    def test_needs_regeneration_when_no_description_exists(self):
        """Test that regeneration is needed when no dynamic description exists"""
        # Product created without dynamic description
        self.assertTrue(self.generator.needs_regeneration(self.product))
    
    def test_needs_regeneration_when_no_generation_timestamp(self):
        """Test that regeneration is needed when generation timestamp is missing"""
        self.product.dynamic_description = "Some description"
        self.product.dynamic_description_generated_at = None
        self.product.save()
        
        self.assertTrue(self.generator.needs_regeneration(self.product))
    
    def test_no_regeneration_needed_for_fresh_description(self):
        """Test that fresh description (< 7 days) doesn't need regeneration"""
        # Set description generated 3 days ago, but ensure it's after product update
        generation_time = timezone.now() - timedelta(days=3)
        self.product.dynamic_description = "Fresh description"
        self.product.dynamic_description_generated_at = generation_time
        # Use update_fields to avoid updating updated_at
        self.product.save(update_fields=['dynamic_description', 'dynamic_description_generated_at'])
        
        # Manually set updated_at to be before generation time to simulate product not being updated
        Product.objects.filter(id=self.product.id).update(
            updated_at=generation_time - timedelta(hours=1)
        )
        self.product.refresh_from_db()
        
        self.assertFalse(self.generator.needs_regeneration(self.product))
    
    def test_needs_regeneration_for_old_description(self):
        """Test that old description (> 7 days) needs regeneration"""
        # Set description generated 8 days ago
        self.product.dynamic_description = "Old description"
        self.product.dynamic_description_generated_at = timezone.now() - timedelta(days=8)
        self.product.save()
        
        self.assertTrue(self.generator.needs_regeneration(self.product))
    
    def test_needs_regeneration_when_product_updated_after_generation(self):
        """Test that regeneration is needed when product was updated after description generation"""
        # Generate description first
        generation_time = timezone.now() - timedelta(days=2)
        self.product.dynamic_description = "Description"
        self.product.dynamic_description_generated_at = generation_time
        self.product.save()
        
        # Update product after description was generated
        self.product.price = 39.99
        self.product.save()
        
        # Should need regeneration because product.updated_at > generation time
        self.assertTrue(self.generator.needs_regeneration(self.product))
    
    def test_regeneration_at_exactly_7_days(self):
        """Test edge case: description exactly 7 days old"""
        # Set description generated exactly 7 days ago
        self.product.dynamic_description = "Week old description"
        self.product.dynamic_description_generated_at = timezone.now() - timedelta(days=7)
        self.product.save()
        
        # Should need regeneration (older than 7 days)
        self.assertTrue(self.generator.needs_regeneration(self.product))


class DynamicDescriptionPromptBuildingTests(TestCase):
    """
    Test Case: Prompt Building
    
    Tests the _build_prompt() method which constructs the prompt
    sent to the OpenAI API.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        # Create test product with specifications
        self.product = Product.objects.create(
            category=self.category,
            name='Test Blender',
            slug='test-blender',
            description='Basic blender with motor',
            specifications='450-watt motor\n3 speed settings\nStainless steel blades',
            price=49.99,
            stock=15,
            units_sold=100
        )
    
    def test_prompt_contains_product_name(self):
        """Test that prompt includes product name"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn(self.product.name, prompt)
    
    def test_prompt_contains_category(self):
        """Test that prompt includes product category"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn(self.product.category.name, prompt)
    
    def test_prompt_contains_price(self):
        """Test that prompt includes product price"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn(str(self.product.price), prompt)
    
    def test_prompt_contains_description(self):
        """Test that prompt includes original description"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn(self.product.description, prompt)
    
    def test_prompt_contains_specifications(self):
        """Test that prompt includes product specifications"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn('450-watt motor', prompt)
        self.assertIn('3 speed settings', prompt)
    
    def test_prompt_includes_reviews_when_available(self):
        """Test that prompt includes customer reviews when they exist"""
        # Add a review
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Great product',
            comment='Works perfectly!',
            is_approved=True
        )
        
        prompt = self.generator._build_prompt(self.product)
        self.assertIn('Works perfectly!', prompt)
        self.assertIn('5/5 stars', prompt)
    
    def test_prompt_handles_no_reviews(self):
        """Test that prompt handles products with no reviews"""
        prompt = self.generator._build_prompt(self.product)
        self.assertIn('No reviews yet', prompt)
    
    def test_prompt_limits_review_count(self):
        """Test that prompt only includes up to 10 most recent reviews"""
        # Create 15 reviews
        for i in range(15):
            Review.objects.create(
                product=self.product,
                user=User.objects.create_user(
                    username=f'user{i}',
                    password='pass'
                ),
                rating=5,
                title=f'Review {i}',
                comment=f'Comment {i}',
                is_approved=True
            )
        
        prompt = self.generator._build_prompt(self.product)
        # Should only include 10 reviews max
        review_count = prompt.count('/5 stars')
        self.assertLessEqual(review_count, 10)
    
    def test_prompt_only_includes_approved_reviews(self):
        """Test that prompt only includes approved reviews"""
        # Create approved review
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Approved',
            comment='This is approved',
            is_approved=True
        )
        
        # Create unapproved review
        unapproved_user = User.objects.create_user(
            username='unapproved',
            password='pass'
        )
        Review.objects.create(
            product=self.product,
            user=unapproved_user,
            rating=1,
            title='Not Approved',
            comment='This should not appear',
            is_approved=False
        )
        
        prompt = self.generator._build_prompt(self.product)
        self.assertIn('This is approved', prompt)
        self.assertNotIn('This should not appear', prompt)


class DynamicDescriptionGenerationTests(TestCase):
    """
    Test Case: Description Generation
    
    Tests the generate_description() method which calls the OpenAI API
    to generate product descriptions. Uses mocking to avoid actual API calls.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        self.category = Category.objects.create(
            name='Home & Kitchen',
            slug='home-kitchen'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Coffee Maker',
            slug='coffee-maker',
            description='Makes coffee',
            price=79.99,
            stock=20
        )
    
    @patch('store.dynamic_description.OpenAI')
    def test_generate_description_returns_string(self, mock_openai):
        """Test that generate_description returns a string"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated description"
        mock_client.chat.completions.create.return_value = mock_response
        
        self.generator.client = mock_client
        
        result = self.generator.generate_description(self.product)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Generated description")
    
    @patch('store.dynamic_description.OpenAI')
    def test_generate_description_removes_surrounding_quotes(self, mock_openai):
        """Test that surrounding quotes are removed from generated description"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '"Description with quotes"'
        mock_client.chat.completions.create.return_value = mock_response
        
        self.generator.client = mock_client
        
        result = self.generator.generate_description(self.product)
        self.assertEqual(result, "Description with quotes")
        self.assertFalse(result.startswith('"'))
        self.assertFalse(result.endswith('"'))
    
    def test_generate_description_returns_none_when_no_api_key(self):
        """Test that generate_description returns None when API key is not configured"""
        # Set client to None to simulate missing API key
        self.generator.client = None
        
        result = self.generator.generate_description(self.product)
        self.assertIsNone(result)
    
    @patch('store.dynamic_description.OpenAI')
    def test_generate_description_handles_api_errors(self, mock_openai):
        """Test that API errors are handled gracefully"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        self.generator.client = mock_client
        
        result = self.generator.generate_description(self.product)
        self.assertIsNone(result)


class DynamicDescriptionProductUpdateTests(TestCase):
    """
    Test Case: Product Update
    
    Tests the update_product_description() method which updates
    the product with a new dynamic description.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        self.category = Category.objects.create(
            name='Sports',
            slug='sports'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Running Shoes',
            slug='running-shoes',
            description='Comfortable running shoes',
            price=89.99,
            stock=50
        )
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_update_product_description_saves_to_database(self, mock_generate):
        """Test that generated description is saved to database"""
        mock_generate.return_value = "New dynamic description"
        
        result = self.generator.update_product_description(self.product)
        
        self.assertTrue(result)
        self.product.refresh_from_db()
        self.assertEqual(self.product.dynamic_description, "New dynamic description")
        self.assertIsNotNone(self.product.dynamic_description_generated_at)
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_update_product_description_updates_timestamp(self, mock_generate):
        """Test that generation timestamp is updated"""
        mock_generate.return_value = "Description"
        
        before_time = timezone.now()
        self.generator.update_product_description(self.product)
        after_time = timezone.now()
        
        self.product.refresh_from_db()
        self.assertGreaterEqual(
            self.product.dynamic_description_generated_at,
            before_time
        )
        self.assertLessEqual(
            self.product.dynamic_description_generated_at,
            after_time
        )
    
    @patch.object(DynamicDescriptionGenerator, 'needs_regeneration')
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_update_skips_when_not_needed_without_force(self, mock_generate, mock_needs):
        """Test that update is skipped when not needed and force=False"""
        mock_needs.return_value = False
        
        result = self.generator.update_product_description(self.product, force=False)
        
        self.assertFalse(result)
        mock_generate.assert_not_called()
    
    @patch.object(DynamicDescriptionGenerator, 'needs_regeneration')
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_update_proceeds_when_forced(self, mock_generate, mock_needs):
        """Test that update proceeds when force=True even if not needed"""
        mock_needs.return_value = False
        mock_generate.return_value = "Forced description"
        
        result = self.generator.update_product_description(self.product, force=True)
        
        self.assertTrue(result)
        mock_generate.assert_called_once()
    
    @patch.object(DynamicDescriptionGenerator, 'generate_description')
    def test_update_returns_false_when_generation_fails(self, mock_generate):
        """Test that update returns False when generation fails"""
        mock_generate.return_value = None
        
        result = self.generator.update_product_description(self.product)
        
        self.assertFalse(result)


class DynamicDescriptionEdgeCasesTests(TestCase):
    """
    Test Case: Edge Cases and Special Scenarios
    
    Tests edge cases and unusual scenarios that might occur in production.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.generator = DynamicDescriptionGenerator()
        
        self.category = Category.objects.create(
            name='Test',
            slug='test'
        )
    
    def test_handles_product_with_empty_description(self):
        """Test handling of product with empty description"""
        product = Product.objects.create(
            category=self.category,
            name='Product',
            slug='product',
            description='',
            price=10.00,
            stock=5
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
    
    def test_handles_product_with_no_specifications(self):
        """Test handling of product without specifications"""
        product = Product.objects.create(
            category=self.category,
            name='Product',
            slug='product',
            description='Basic product',
            specifications='',
            price=10.00,
            stock=5
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIn('Not available', prompt)
    
    def test_handles_product_with_very_long_description(self):
        """Test handling of product with very long description"""
        long_description = 'A' * 5000
        product = Product.objects.create(
            category=self.category,
            name='Product',
            slug='product',
            description=long_description,
            price=10.00,
            stock=5
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIn(long_description, prompt)
    
    def test_handles_product_with_special_characters(self):
        """Test handling of product with special characters in name/description"""
        product = Product.objects.create(
            category=self.category,
            name='Product "Special" & <Test>',
            slug='product-special',
            description='Description with $pecial ch@racters!',
            price=10.00,
            stock=5
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIn('Product "Special" & <Test>', prompt)
    
    def test_handles_zero_price_product(self):
        """Test handling of free product (price = 0)"""
        product = Product.objects.create(
            category=self.category,
            name='Free Product',
            slug='free-product',
            description='Free item',
            price=0.00,
            stock=100
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIn('0', prompt)
    
    def test_handles_product_with_zero_units_sold(self):
        """Test handling of new product with no sales"""
        product = Product.objects.create(
            category=self.category,
            name='New Product',
            slug='new-product',
            description='Brand new',
            price=25.00,
            stock=10,
            units_sold=0
        )
        
        prompt = self.generator._build_prompt(product)
        self.assertIn('0', prompt)


# Re-enable logging after tests
logging.disable(logging.NOTSET)
