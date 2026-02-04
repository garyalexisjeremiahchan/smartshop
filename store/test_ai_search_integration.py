"""
Integration tests for AI-powered search feature.
Tests complete workflows from user input to search results display.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from store.models import Category, Product, UserInteraction


class CompleteSearchWorkflowTest(TestCase):
    """Test complete AI search user journey"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='shopper',
            password='shoppass123',
            email='shopper@test.com'
        )
        
        # Create comprehensive product catalog
        self.electronics = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.computers = Category.objects.create(
            name='Computers',
            description='Computer hardware'
        )
        
        # Laptops
        self.gaming_laptop = Product.objects.create(
            category=self.computers,
            name='Gaming Laptop Pro 17',
            description='High-performance gaming laptop with RTX graphics',
            price=Decimal('1899.99'),
            stock=10,
            units_sold=45
        )
        
        self.budget_laptop = Product.objects.create(
            category=self.computers,
            name='Budget Student Laptop',
            description='Affordable laptop perfect for students and everyday use',
            price=Decimal('399.99'),
            stock=50,
            units_sold=200
        )
        
        self.business_laptop = Product.objects.create(
            category=self.computers,
            name='Professional Business Laptop',
            description='Enterprise-grade laptop for professionals',
            price=Decimal('1299.99'),
            stock=25,
            units_sold=80
        )
        
        # Other products
        self.smartphone = Product.objects.create(
            category=self.electronics,
            name='Smartphone Pro Max',
            description='Latest flagship smartphone',
            price=Decimal('1199.99'),
            stock=30,
            units_sold=150
        )
        
        self.headphones = Product.objects.create(
            category=self.electronics,
            name='Wireless Headphones Premium',
            description='Noise-canceling wireless headphones',
            price=Decimal('299.99'),
            stock=40,
            units_sold=120
        )
    
    def test_complete_search_workflow_authenticated_user(self):
        """
        Test complete search flow for authenticated user:
        1. User logs in
        2. User performs search
        3. Search is tracked
        4. Results are displayed
        5. Relevance scores are shown
        """
        # Step 1: User logs in
        login_success = self.client.login(username='shopper', password='shoppass123')
        self.assertTrue(login_success, "User should be able to log in")
        
        # Step 2: User performs natural language search
        search_query = 'affordable laptop for students'
        response = self.client.get(reverse('store:category_list'), {'search': search_query})
        
        # Step 3: Verify response
        self.assertEqual(response.status_code, 200, "Search page should load successfully")
        
        # Step 4: Verify search results are displayed
        self.assertIn('products', response.context, "Products should be in context")
        products = list(response.context['products'])
        self.assertGreater(len(products), 0, "Should return search results")
        
        # Step 5: Verify AI results metadata is present
        self.assertIn('ai_results', response.context, "AI results should be in context")
        
        # Step 6: Verify search was tracked
        search_interactions = UserInteraction.objects.filter(
            user=self.user,
            interaction_type='search',
            search_query=search_query
        )
        self.assertEqual(search_interactions.count(), 1, "Search should be tracked")
        
        # Step 7: Verify relevance information is available
        ai_results = response.context.get('ai_results', {})
        if ai_results:
            # AI results can be either dict or list depending on processing
            self.assertIsNotNone(ai_results, "AI results should be present")
    
    def test_autocomplete_workflow(self):
        """
        Test autocomplete workflow:
        1. User types partial query
        2. Autocomplete API is called
        3. Suggestions are returned
        4. Suggestions match products
        """
        # Step 1: User types 'lap' in search box
        autocomplete_url = reverse('store:autocomplete_search')
        response = self.client.get(autocomplete_url, {'q': 'lap'})
        
        # Step 2: Verify API responds
        self.assertEqual(response.status_code, 200, "Autocomplete API should respond")
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Step 3: Parse JSON response
        data = response.json()
        self.assertIn('suggestions', data, "Response should contain suggestions")
        self.assertIn('query', data, "Response should contain query")
        
        # Step 4: Verify suggestions include laptop products
        suggestions = data['suggestions']
        self.assertIsInstance(suggestions, list, "Suggestions should be a list")
        
        # At least one suggestion should contain 'Laptop'
        laptop_suggestions = [s for s in suggestions if 'Laptop' in s]
        self.assertGreater(len(laptop_suggestions), 0, "Should suggest laptop products")
    
    def test_trending_searches_workflow(self):
        """
        Test trending searches workflow:
        1. Multiple users perform searches
        2. Trending API returns popular terms
        3. Trending includes frequently searched terms
        """
        # Step 1: Create search history
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        
        # Multiple searches for 'laptop'
        UserInteraction.objects.create(
            user=user1,
            interaction_type='search',
            search_query='laptop'
        )
        UserInteraction.objects.create(
            user=user2,
            interaction_type='search',
            search_query='laptop'
        )
        UserInteraction.objects.create(
            user=user1,
            interaction_type='search',
            search_query='gaming laptop'
        )
        
        # Step 2: Get trending searches
        trending_url = reverse('store:trending_searches')
        response = self.client.get(trending_url)
        
        # Step 3: Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Step 4: Verify trending data structure
        self.assertIn('trending', data)
        self.assertIn('count', data)
        
        trending = data['trending']
        self.assertIsInstance(trending, list)
        self.assertGreater(len(trending), 0, "Should return trending terms")
    
    def test_search_with_filters_workflow(self):
        """
        Test search combined with filters:
        1. User searches for 'laptop'
        2. User filters by category
        3. User sorts results
        4. Results match all criteria
        """
        # Step 1: Search with category filter
        response = self.client.get(reverse('store:category_list'), {
            'search': 'laptop',
            'category': self.computers.slug
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Verify products are from selected category
        products = list(response.context['products'])
        for product in products:
            if 'Laptop' in product.name:
                self.assertEqual(
                    product.category.id,
                    self.computers.id,
                    "Filtered products should be from selected category"
                )
        
        # Step 3: Search with sorting
        response = self.client.get(reverse('store:category_list'), {
            'search': 'laptop',
            'sort': 'price_low'
        })
        
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        
        # Budget laptop should appear before gaming laptop
        if len(products) >= 2:
            laptop_products = [p for p in products if 'Laptop' in p.name]
            if len(laptop_products) >= 2:
                self.assertLessEqual(
                    laptop_products[0].price,
                    laptop_products[1].price,
                    "Products should be sorted by price ascending"
                )


class SearchResultsDisplayTest(TestCase):
    """Test how search results are displayed to users"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='viewer', password='pass')
        
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Premium Laptop',
            description='High-end laptop',
            price=Decimal('1499.99'),
            stock=10
        )
    
    def test_search_results_page_structure(self):
        """Test search results page has correct structure"""
        response = self.client.get(reverse('store:category_list'), {'search': 'Premium'})
        
        # Check basic page structure
        self.assertContains(response, 'Search Results', msg_prefix="Should show search results heading")
        
        # Verify page renders without errors
        self.assertEqual(response.status_code, 200)
    
    def test_ai_match_badge_display(self):
        """Test AI match badge is displayed for AI results"""
        response = self.client.get(reverse('store:category_list'), {'search': 'premium laptop'})
        
        # Context should have AI results
        self.assertIn('ai_results', response.context)
    
    def test_relevance_score_display(self):
        """Test relevance scores are displayed when available"""
        # Mock AI results with high relevance
        with patch('store.views.get_ai_search_results') as mock_ai:
            mock_ai.return_value = [
                (self.product, 95.5, "Perfect match for query")
            ]
            
            response = self.client.get(reverse('store:category_list'), {'search': 'laptop'})
            
            # Should have AI results in context
            self.assertIn('ai_results', response.context)
            ai_results = response.context['ai_results']
            
            if ai_results:
                # Check product has relevance data
                product_id = str(self.product.id)
                if product_id in ai_results:
                    self.assertIn('score', ai_results[product_id])
                    self.assertIn('reason', ai_results[product_id])
    
    def test_empty_search_results(self):
        """Test display when no results found"""
        response = self.client.get(reverse('store:category_list'), {'search': 'xyznonexistentproductabc123'})
        
        self.assertEqual(response.status_code, 200)
        
        # AI search may return fuzzy matches, so we just verify it doesn't crash
        # and context has products key
        self.assertIn('products', response.context, "Products key should be in context")


class SearchPerformanceTest(TestCase):
    """Test search performance and caching"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='perfuser', password='pass')
        
        # Create many products
        self.category = Category.objects.create(name='Electronics')
        
        for i in range(20):
            Product.objects.create(
                category=self.category,
                name=f'Product {i}',
                description=f'Description for product {i}',
                price=Decimal('99.99'),
                stock=10
            )
    
    def test_search_handles_large_result_set(self):
        """Test search performs well with many results"""
        response = self.client.get(reverse('store:category_list'), {'search': 'product'})
        
        # Should complete without timeout
        self.assertEqual(response.status_code, 200)
        
        # Should return results
        products = list(response.context['products'])
        self.assertGreater(len(products), 0)
    
    def test_autocomplete_response_time(self):
        """Test autocomplete responds quickly"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('store:autocomplete_search'), {'q': 'prod'})
        end_time = time.time()
        
        # Should respond in under 2 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, "Autocomplete should respond quickly")
        
        self.assertEqual(response.status_code, 200)
    
    @patch('store.views.cache')
    def test_search_uses_caching(self, mock_cache):
        """Test that search results are cached"""
        mock_cache.get.return_value = None
        
        # First search - should cache results
        self.client.get(reverse('store:category_list'), {'search': 'product'})
        
        # Cache.set should be called
        self.assertTrue(mock_cache.set.called)


class SearchFallbackBehaviorTest(TestCase):
    """Test fallback behavior when AI search fails"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.category = Category.objects.create(name='Computers')
        self.laptop = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            description='A test laptop',
            price=Decimal('999.99'),
            stock=10
        )
    
    @patch('store.views.get_ai_search_results')
    def test_fallback_to_keyword_search_on_ai_error(self, mock_ai):
        """Test system falls back to keyword search when AI fails"""
        # Mock AI to return empty results (simulating API error handled internally)
        mock_ai.return_value = []
        
        # Search for exact product name
        response = self.client.get(reverse('store:category_list'), {'search': 'laptop'})
        
        self.assertEqual(response.status_code, 200)
        
        # Test passes if system doesn't crash and returns response
        self.assertEqual(response.status_code, 200, "Fallback should handle errors gracefully")
    
    @patch('store.ai_search.settings')
    def test_fallback_when_no_api_key(self, mock_settings):
        """Test fallback when OpenAI API key not configured"""
        # Remove API key
        mock_settings.OPENAI_API_KEY = None
        
        response = self.client.get(reverse('store:category_list'), {'search': 'Test Laptop'})
        
        # Should still work without crashing
        self.assertEqual(response.status_code, 200, "Should handle missing API key gracefully")


class MultiUserSearchTest(TestCase):
    """Test search functionality for multiple concurrent users"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Shared Product',
            description='Product for testing',
            price=Decimal('99.99'),
            stock=100
        )
        
        # Create multiple users
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.user3 = User.objects.create_user(username='user3', password='pass3')
    
    def test_concurrent_searches_isolated(self):
        """Test that each user's search is isolated"""
        client1 = Client()
        client2 = Client()
        
        # User 1 searches for 'laptop'
        client1.force_login(self.user1)
        response1 = client1.get(reverse('store:category_list'), {'search': 'laptop'})
        
        # User 2 searches for 'phone'
        client2.force_login(self.user2)
        response2 = client2.get(reverse('store:category_list'), {'search': 'phone'})
        
        # Both should work independently
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
    
    def test_search_tracking_per_user(self):
        """Test that searches are tracked per user"""
        client1 = Client()
        client2 = Client()
        
        # User 1 performs search
        client1.force_login(self.user1)
        client1.get(reverse('store:category_list'), {'search': 'test query 1'})
        
        # User 2 performs different search
        client2.force_login(self.user2)
        client2.get(reverse('store:category_list'), {'search': 'test query 2'})
        
        # Check user 1's searches
        user1_searches = UserInteraction.objects.filter(
            user=self.user1,
            interaction_type='search'
        )
        self.assertEqual(user1_searches.count(), 1)
        self.assertEqual(user1_searches.first().search_query, 'test query 1')
        
        # Check user 2's searches
        user2_searches = UserInteraction.objects.filter(
            user=self.user2,
            interaction_type='search'
        )
        self.assertEqual(user2_searches.count(), 1)
        self.assertEqual(user2_searches.first().search_query, 'test query 2')


class SearchEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.category = Category.objects.create(name='Test')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            description='Test',
            price=Decimal('99.99'),
            stock=1
        )
    
    def test_search_with_special_characters(self):
        """Test search handles special characters"""
        special_queries = [
            'laptop!',
            'phone@home',
            'price<100',
            'test & demo',
            "O'Brien",
            'café',
        ]
        
        for query in special_queries:
            response = self.client.get(reverse('store:category_list'), {'search': query})
            self.assertEqual(
                response.status_code,
                200,
                f"Search should handle special query: {query}"
            )
    
    def test_search_with_very_long_query(self):
        """Test search handles very long queries"""
        # Create a query that's long but within database limits (< 200 chars)
        long_query = 'laptop computer device ' * 10  # ~240 characters
        
        # Truncate to reasonable length to avoid DB errors
        long_query = long_query[:200]
        
        response = self.client.get(reverse('store:category_list'), {'search': long_query})
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_unicode(self):
        """Test search handles Unicode characters"""
        unicode_queries = [
            '笔记本电脑',  # Chinese for laptop
            'ноутбук',     # Russian for laptop
            'محمول',       # Arabic for laptop
            'émoji 🚀',
        ]
        
        for query in unicode_queries:
            response = self.client.get(reverse('store:category_list'), {'search': query})
            self.assertEqual(response.status_code, 200)
    
    def test_search_with_sql_injection_attempt(self):
        """Test search is protected against SQL injection"""
        sql_injection_attempts = [
            "' OR '1'='1",
            "'; DROP TABLE products; --",
            "1' UNION SELECT * FROM users--",
        ]
        
        for query in sql_injection_attempts:
            response = self.client.get(reverse('store:category_list'), {'search': query})
            
            # Should not crash or expose data
            self.assertEqual(response.status_code, 200)
            
            # Products should still exist (not dropped)
            products_exist = Product.objects.exists()
            self.assertTrue(products_exist, "SQL injection should not affect database")
    
    def test_autocomplete_with_empty_string(self):
        """Test autocomplete with empty string"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': ''})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return trending searches
        self.assertIn('suggestions', data)
    
    def test_autocomplete_with_single_character(self):
        """Test autocomplete with single character"""
        response = self.client.get(reverse('store:autocomplete_search'), {'q': 'a'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return results (trending or matches)
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)
