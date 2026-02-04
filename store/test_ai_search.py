"""
Unit tests for AI-powered search functionality.
Tests the AI search engine, autocomplete, and trending search features.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from store.models import Category, Product, UserInteraction
from store.ai_search import (
    get_ai_search_results,
    fallback_search,
    get_trending_searches,
    get_autocomplete_suggestions
)


class AISearchFunctionsTest(TestCase):
    """Test AI search utility functions"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='searchuser',
            password='testpass123',
            email='search@test.com'
        )
        
        # Create categories
        self.electronics = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.computers = Category.objects.create(
            name='Computers',
            description='Computer products'
        )
        
        # Create products
        self.laptop = Product.objects.create(
            category=self.computers,
            name='Gaming Laptop Pro',
            description='High-performance laptop for gaming',
            price=Decimal('1299.99'),
            stock=10,
            units_sold=50
        )
        
        self.budget_laptop = Product.objects.create(
            category=self.computers,
            name='Budget Laptop',
            description='Affordable laptop for students',
            price=Decimal('399.99'),
            stock=20,
            units_sold=100
        )
        
        self.smartphone = Product.objects.create(
            category=self.electronics,
            name='Smartphone Pro',
            description='Latest smartphone with advanced features',
            price=Decimal('899.99'),
            stock=15,
            units_sold=75
        )
        
        self.headphones = Product.objects.create(
            category=self.electronics,
            name='Wireless Headphones',
            description='Premium wireless headphones',
            price=Decimal('199.99'),
            stock=30,
            units_sold=120
        )
    
    def test_fallback_search_by_product_name(self):
        """Test fallback search finds products by name"""
        results = fallback_search('laptop', limit=10)
        
        # Should find both laptops
        self.assertEqual(len(results), 2)
        
        # Results should be tuples of (product, score, reason)
        product, score, reason = results[0]
        self.assertIn('Laptop', product.name)
        self.assertGreaterEqual(score, 60.0)
        self.assertEqual(reason, "Keyword match")
    
    def test_fallback_search_by_category(self):
        """Test fallback search finds products by category"""
        results = fallback_search('electronics', limit=10)
        
        # Should find electronics products
        self.assertGreater(len(results), 0)
        
        for product, score, reason in results:
            self.assertEqual(product.category.name, 'Electronics')
    
    def test_fallback_search_case_insensitive(self):
        """Test fallback search is case-insensitive"""
        results_lower = fallback_search('laptop', limit=10)
        results_upper = fallback_search('LAPTOP', limit=10)
        results_mixed = fallback_search('LapTop', limit=10)
        
        # All should return same results
        self.assertEqual(len(results_lower), len(results_upper))
        self.assertEqual(len(results_lower), len(results_mixed))
    
    def test_fallback_search_respects_limit(self):
        """Test fallback search respects limit parameter"""
        results = fallback_search('product', limit=2)
        
        self.assertLessEqual(len(results), 2)
    
    def test_fallback_search_no_results(self):
        """Test fallback search returns empty list when no matches"""
        results = fallback_search('nonexistent-product-xyz', limit=10)
        
        self.assertEqual(len(results), 0)
    
    @patch('store.ai_search.OpenAI')
    def test_ai_search_results_with_mock(self, mock_openai):
        """Test AI search with mocked OpenAI response"""
        # Mock OpenAI API response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps([
            {
                "product_id": self.laptop.id,
                "relevance_score": 95.5,
                "reason": "Perfect match for gaming laptop"
            },
            {
                "product_id": self.budget_laptop.id,
                "relevance_score": 85.0,
                "reason": "Affordable laptop option"
            }
        ])
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test AI search
        with patch('store.ai_search.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = 'test-key'
            mock_settings.OPENAI_MODEL = 'gpt-4o-mini'
            
            results = get_ai_search_results('cheap laptop for students', user=self.user, limit=10)
        
        # Should return results
        self.assertEqual(len(results), 2)
        
        # Verify result structure
        product, score, reason = results[0]
        self.assertEqual(product.id, self.laptop.id)
        self.assertEqual(score, 95.5)
        self.assertIn('gaming laptop', reason.lower())
    
    @patch('store.ai_search.OpenAI')
    def test_ai_search_falls_back_on_error(self, mock_openai):
        """Test AI search falls back to keyword search on API error"""
        # Mock OpenAI to raise an exception
        mock_openai.side_effect = Exception("API Error")
        
        with patch('store.ai_search.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = 'test-key'
            
            results = get_ai_search_results('laptop', user=self.user, limit=10)
        
        # Should still return results via fallback
        self.assertGreater(len(results), 0)
        
        # Results should be from fallback search
        for product, score, reason in results:
            self.assertIn('Laptop', product.name)
    
    def test_get_trending_searches_with_interactions(self):
        """Test trending searches based on user interactions"""
        # Create search interactions
        UserInteraction.objects.create(
            user=self.user,
            interaction_type='search',
            search_query='laptop'
        )
        UserInteraction.objects.create(
            user=self.user,
            interaction_type='search',
            search_query='laptop'
        )
        UserInteraction.objects.create(
            user=self.user,
            interaction_type='search',
            search_query='smartphone'
        )
        
        trending = get_trending_searches(user=None, limit=10)
        
        # Should return trending terms
        self.assertGreater(len(trending), 0)
        
        # Should include popular search terms or product names
        self.assertIsInstance(trending, list)
        for term in trending:
            self.assertIsInstance(term, str)
    
    def test_get_trending_searches_includes_products(self):
        """Test trending searches includes popular products"""
        trending = get_trending_searches(user=None, limit=5)
        
        # Should return product names from popular products
        self.assertGreater(len(trending), 0)
        
        # At least one trending term should match a product name
        product_names = [p.name for p in Product.objects.all()]
        has_product = any(term in product_names for term in trending)
        self.assertTrue(has_product, "Trending should include product names")
    
    def test_get_autocomplete_suggestions_short_query(self):
        """Test autocomplete returns trending for queries < 2 chars"""
        suggestions = get_autocomplete_suggestions('l', user=None, limit=8)
        
        # Should return trending searches for short query
        self.assertIsInstance(suggestions, list)
    
    def test_get_autocomplete_suggestions_matches_products(self):
        """Test autocomplete finds matching products"""
        suggestions = get_autocomplete_suggestions('lap', user=None, limit=8)
        
        # Should find laptop products
        self.assertGreater(len(suggestions), 0)
        
        # At least one suggestion should contain 'Laptop'
        has_laptop = any('Laptop' in s for s in suggestions)
        self.assertTrue(has_laptop, "Autocomplete should find laptop products")
    
    def test_get_autocomplete_suggestions_matches_categories(self):
        """Test autocomplete finds matching categories"""
        suggestions = get_autocomplete_suggestions('comp', user=None, limit=8)
        
        # Should find Computers category
        self.assertIn('Computers', suggestions)
    
    def test_get_autocomplete_suggestions_respects_limit(self):
        """Test autocomplete respects limit parameter"""
        suggestions = get_autocomplete_suggestions('pro', user=None, limit=3)
        
        self.assertLessEqual(len(suggestions), 3)


class AISearchViewsTest(TestCase):
    """Test AI search API endpoints"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test products
        self.category = Category.objects.create(name='Electronics')
        self.product1 = Product.objects.create(
            category=self.category,
            name='Laptop Pro',
            description='Professional laptop',
            price=Decimal('999.99'),
            stock=10
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='Laptop Gaming',
            description='Gaming laptop',
            price=Decimal('1499.99'),
            stock=5
        )
    
    def test_autocomplete_api_endpoint_exists(self):
        """Test autocomplete API endpoint is accessible"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': 'lap'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_autocomplete_api_returns_suggestions(self):
        """Test autocomplete API returns valid JSON with suggestions"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': 'lap'})
        
        data = response.json()
        
        # Check response structure
        self.assertIn('suggestions', data)
        self.assertIn('query', data)
        self.assertEqual(data['query'], 'lap')
        
        # Suggestions should be a list
        self.assertIsInstance(data['suggestions'], list)
    
    def test_autocomplete_api_finds_products(self):
        """Test autocomplete API finds matching products"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': 'laptop'})
        
        data = response.json()
        suggestions = data['suggestions']
        
        # Should find laptop products
        self.assertGreater(len(suggestions), 0)
        
        # At least one suggestion should be a laptop
        has_laptop = any('Laptop' in s for s in suggestions)
        self.assertTrue(has_laptop)
    
    def test_autocomplete_api_empty_query(self):
        """Test autocomplete API with empty query returns trending"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': ''})
        
        data = response.json()
        
        # Should return trending searches
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)
    
    def test_autocomplete_api_no_query_parameter(self):
        """Test autocomplete API without query parameter"""
        response = self.client.get(reverse('store:autocomplete_search'))
        
        data = response.json()
        
        # Should handle missing parameter gracefully
        self.assertIn('suggestions', data)
    
    def test_trending_api_endpoint_exists(self):
        """Test trending searches API endpoint is accessible"""
        response = self.client.get(reverse('store:trending_searches'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_trending_api_returns_trending_searches(self):
        """Test trending API returns valid JSON with trending searches"""
        response = self.client.get(reverse('store:trending_searches'))
        
        data = response.json()
        
        # Check response structure
        self.assertIn('trending', data)
        self.assertIn('count', data)
        
        # Trending should be a list
        self.assertIsInstance(data['trending'], list)
        self.assertEqual(data['count'], len(data['trending']))
    
    def test_trending_api_respects_limit(self):
        """Test trending API respects limit parameter"""
        response = self.client.get(reverse('store:trending_searches'), {'limit': 5})
        
        data = response.json()
        
        self.assertLessEqual(len(data['trending']), 5)
    
    def test_trending_api_default_limit(self):
        """Test trending API uses default limit when not specified"""
        response = self.client.get(reverse('store:trending_searches'))
        
        data = response.json()
        
        # Default limit is 10
        self.assertLessEqual(len(data['trending']), 10)


class AISearchIntegrationTest(TestCase):
    """Integration tests for AI search in category_list view"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='searchuser',
            password='testpass123'
        )
        
        # Create test data
        self.category = Category.objects.create(name='Computers')
        
        self.laptop1 = Product.objects.create(
            category=self.category,
            name='Gaming Laptop',
            description='High-performance gaming laptop',
            price=Decimal('1299.99'),
            stock=10,
            units_sold=50
        )
        
        self.laptop2 = Product.objects.create(
            category=self.category,
            name='Budget Laptop',
            description='Affordable laptop for students',
            price=Decimal('399.99'),
            stock=20,
            units_sold=100
        )
        
        self.laptop3 = Product.objects.create(
            category=self.category,
            name='Business Laptop',
            description='Professional laptop for business',
            price=Decimal('899.99'),
            stock=15,
            units_sold=75
        )
    
    def test_category_list_with_search_query(self):
        """Test category list view handles search queries"""
        response = self.client.get(reverse('store:category_list'), {'search': 'laptop'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/category_list.html')
    
    def test_category_list_search_returns_products(self):
        """Test category list search returns matching products"""
        response = self.client.get(reverse('store:category_list'), {'search': 'laptop'})
        
        # Should have products in context
        self.assertIn('products', response.context)
        products = list(response.context['products'])
        
        # Should find laptop products
        self.assertGreater(len(products), 0)
    
    def test_category_list_search_includes_ai_results(self):
        """Test category list includes AI results in context"""
        response = self.client.get(reverse('store:category_list'), {'search': 'cheap laptop'})
        
        # Should have ai_results in context
        self.assertIn('ai_results', response.context)
    
    def test_category_list_without_search(self):
        """Test category list without search query shows all products"""
        response = self.client.get(reverse('store:category_list'))
        
        # Should show all products
        products = list(response.context['products'])
        self.assertEqual(len(products), 3)
    
    def test_search_query_tracked(self):
        """Test search queries are tracked in UserInteraction"""
        self.client.login(username='searchuser', password='testpass123')
        
        initial_count = UserInteraction.objects.filter(
            interaction_type='search'
        ).count()
        
        self.client.get(reverse('store:category_list'), {'search': 'laptop'})
        
        # Should create search interaction
        final_count = UserInteraction.objects.filter(
            interaction_type='search'
        ).count()
        
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify search query is saved
        last_search = UserInteraction.objects.filter(
            interaction_type='search'
        ).latest('timestamp')
        
        self.assertEqual(last_search.search_query, 'laptop')
    
    def test_search_results_display_relevance(self):
        """Test search results page displays AI relevance indicators"""
        response = self.client.get(reverse('store:category_list'), {'search': 'gaming laptop'})
        
        # Page should indicate AI-powered results
        self.assertContains(response, 'Search Results')


class AISearchCachingTest(TestCase):
    """Test caching behavior of AI search"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='cacheuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            stock=10
        )
    
    @patch('store.views.cache')
    def test_search_results_are_cached(self, mock_cache):
        """Test that search results are cached"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        
        self.client.login(username='cacheuser', password='testpass123')
        self.client.get(reverse('store:category_list'), {'search': 'test'})
        
        # Cache.set should be called
        self.assertTrue(mock_cache.set.called)
    
    @patch('store.views.cache')
    def test_cached_results_are_used(self, mock_cache):
        """Test that cached results are retrieved"""
        # Mock cached results
        cached_results = [(self.product, 95.0, "Test reason")]
        mock_cache.get.return_value = cached_results
        
        response = self.client.get(reverse('store:category_list'), {'search': 'test'})
        
        # Cache.get should be called
        self.assertTrue(mock_cache.get.called)
        
        # Should not call cache.set if cache hit
        self.assertFalse(mock_cache.set.called)
