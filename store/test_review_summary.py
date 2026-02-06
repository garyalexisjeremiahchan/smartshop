"""
Unit and Integration Tests for AI-Generated Review Summary Feature

Tests cover:
- Review summary generation
- OpenAI integration
- Summary caching and regeneration logic
- Pros/cons extraction
- Sentiment analysis
- Management command
- Display on product pages
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock
import json

from store.models import Category, Product, Review
from store.review_summary import (
    generate_review_summary,
    should_regenerate_summary
)


class ReviewSummaryGenerationTest(TestCase):
    """Test AI review summary generation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Wireless Headphones',
            description='Premium headphones',
            price=Decimal('149.99'),
            stock=20
        )
        
        # Create users and reviews
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                password='pass123'
            )
            self.users.append(user)
    
    def test_summary_requires_minimum_three_reviews(self):
        """Test summary generation requires at least 3 reviews"""
        # Create only 2 reviews
        Review.objects.create(
            product=self.product,
            user=self.users[0],
            rating=5,
            title='Great',
            comment='Excellent sound quality'
        )
        Review.objects.create(
            product=self.product,
            user=self.users[1],
            rating=4,
            title='Good',
            comment='Nice but pricey'
        )
        
        result = should_regenerate_summary(self.product)
        self.assertFalse(result)
    
    def test_should_regenerate_for_new_product(self):
        """Test should regenerate for product without summary"""
        # Create 3 reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=5,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        self.assertFalse(self.product.review_summary)
        result = should_regenerate_summary(self.product)
        self.assertTrue(result)
    
    def test_should_not_regenerate_if_recent(self):
        """Test should not regenerate if summary is less than 1 day old"""
        # Create reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=5,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        # Set summary as recently generated
        self.product.review_summary = 'Test summary'
        self.product.review_summary_generated_at = timezone.now()
        self.product.review_summary_review_count = 3
        self.product.save()
        
        result = should_regenerate_summary(self.product)
        self.assertFalse(result)
    
    def test_should_regenerate_if_old_with_new_reviews(self):
        """Test should regenerate if summary is old and there are new reviews"""
        # Create initial reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=5,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        # Set summary as old (more than 1 day)
        old_date = timezone.now() - timedelta(days=2)
        self.product.review_summary = 'Old summary'
        self.product.review_summary_generated_at = old_date
        self.product.review_summary_review_count = 3
        self.product.save()
        
        # Add new review
        Review.objects.create(
            product=self.product,
            user=self.users[3],
            rating=4,
            title='New review',
            comment='New comment'
        )
        
        result = should_regenerate_summary(self.product)
        self.assertTrue(result)
    
    @patch('store.review_summary.OpenAI')
    def test_generate_review_summary_with_mock(self, mock_openai):
        """Test summary generation with mocked OpenAI"""
        # Create reviews
        reviews_data = [
            (5, 'Excellent', 'Great sound quality and comfortable'),
            (5, 'Love them', 'Best headphones I ever owned'),
            (4, 'Good', 'Sound is good but battery could be better'),
            (3, 'Okay', 'Decent but overpriced')
        ]
        
        for i, (rating, title, comment) in enumerate(reviews_data):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=rating,
                title=title,
                comment=comment
            )
        
        # Mock OpenAI response
        mock_response = {
            "summary": "Customers appreciate the excellent sound quality and comfort, though some find them pricey. Battery life receives mixed feedback.",
            "pros": [
                "Excellent sound quality",
                "Very comfortable to wear",
                "Great for long listening sessions"
            ],
            "cons": [
                "Battery life could be better",
                "Considered overpriced by some"
            ],
            "sentiment": "positive"
        }
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Generate summary
        result = generate_review_summary(self.product)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['sentiment'], 'positive')
        self.assertEqual(len(result['pros']), 3)
        self.assertEqual(len(result['cons']), 2)
        
        # Verify product fields updated
        self.product.refresh_from_db()
        self.assertIsNotNone(self.product.review_summary)
        self.assertIsNotNone(self.product.review_summary_pros)
        self.assertIsNotNone(self.product.review_summary_cons)
        self.assertEqual(self.product.review_summary_sentiment, 'positive')
        self.assertIsNotNone(self.product.review_summary_generated_at)
        self.assertEqual(self.product.review_summary_review_count, 4)
    
    @patch('store.review_summary.OpenAI')
    def test_generate_summary_handles_api_error(self, mock_openai):
        """Test summary generation handles OpenAI API errors gracefully"""
        # Create reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=5,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        # Mock OpenAI to raise exception
        mock_openai.side_effect = Exception("API Error")
        
        result = generate_review_summary(self.product)
        
        # Should return None on error
        self.assertIsNone(result)
        
        # Product fields should not be updated
        self.product.refresh_from_db()
        self.assertFalse(self.product.review_summary)


class ReviewSummarySentimentTest(TestCase):
    """Test sentiment analysis in review summaries"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Books', slug='books')
        self.product = Product.objects.create(
            category=self.category,
            name='Python Programming Book',
            description='Learn Python',
            price=Decimal('49.99'),
            stock=50
        )
        self.users = [
            User.objects.create_user(username=f'user{i}', password='pass')
            for i in range(5)
        ]
    
    @patch('store.review_summary.OpenAI')
    def test_positive_sentiment_with_high_ratings(self, mock_openai):
        """Test positive sentiment for mostly high-rated reviews"""
        # Create mostly positive reviews
        for i in range(4):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=5,
                title='Excellent',
                comment='Great book, very helpful'
            )
        
        mock_response = {
            "summary": "Highly recommended book",
            "pros": ["Clear explanations", "Good examples"],
            "cons": [],
            "sentiment": "positive"
        }
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_client.chat.completions.create.return_value = mock_completion
        
        generate_review_summary(self.product)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_summary_sentiment, 'positive')
    
    @patch('store.review_summary.OpenAI')
    def test_neutral_sentiment_with_mixed_ratings(self, mock_openai):
        """Test neutral sentiment for mixed reviews"""
        ratings = [5, 4, 3, 3, 2]
        for i, rating in enumerate(ratings):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=rating,
                title='Review',
                comment='Some good, some bad'
            )
        
        mock_response = {
            "summary": "Mixed reviews",
            "pros": ["Good content"],
            "cons": ["Needs more examples"],
            "sentiment": "neutral"
        }
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_client.chat.completions.create.return_value = mock_completion
        
        generate_review_summary(self.product)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_summary_sentiment, 'neutral')


class ReviewSummaryDisplayTest(TestCase):
    """Test review summary display on product pages"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        self.product = Product.objects.create(
            category=self.category,
            name='Smart Watch',
            description='Fitness tracker',
            price=Decimal('199.99'),
            stock=15
        )
        self.users = [
            User.objects.create_user(username=f'user{i}', password='pass')
            for i in range(3)
        ]
        
        # Create reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=4,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
    
    def test_summary_not_displayed_without_minimum_reviews(self):
        """Test summary is not displayed with less than 3 reviews"""
        # Delete one review to have only 2
        Review.objects.filter(product=self.product).first().delete()
        
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertNotContains(response, 'AI Review Summary')
    
    def test_summary_displayed_with_sufficient_reviews(self):
        """Test summary is displayed when product has 3+ reviews and summary exists"""
        # Set summary data
        self.product.review_summary = 'Great product with excellent features'
        self.product.review_summary_pros = 'Good battery\nNice display\nComfortable'
        self.product.review_summary_cons = 'Expensive\nLimited apps'
        self.product.review_summary_sentiment = 'positive'
        self.product.review_summary_generated_at = timezone.now()
        self.product.review_summary_review_count = 3
        self.product.save()
        
        response = self.client.get(f'/product/{self.product.slug}/')
        
        # Check summary is displayed
        self.assertContains(response, 'AI Review Summary')
        self.assertContains(response, 'Great product with excellent features')
        self.assertContains(response, 'What Customers Like')
        self.assertContains(response, 'Common Concerns')
        self.assertContains(response, 'Good battery')
        self.assertContains(response, 'Expensive')
    
    def test_summary_shows_review_count_badge(self):
        """Test summary displays review count badge"""
        self.product.review_summary = 'Summary'
        self.product.review_summary_generated_at = timezone.now()
        self.product.review_summary_review_count = 3
        self.product.save()
        
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertContains(response, 'Based on 3 reviews')
    
    def test_summary_shows_sentiment_badge(self):
        """Test summary displays appropriate sentiment badge"""
        self.product.review_summary = 'Summary'
        self.product.review_summary_sentiment = 'positive'
        self.product.review_summary_generated_at = timezone.now()
        self.product.review_summary_review_count = 3
        self.product.save()
        
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertContains(response, 'Mostly Positive Feedback')


class ReviewSummaryManagementCommandTest(TransactionTestCase):
    """Test the generate_review_summaries management command"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Test', slug='test')
        
        # Create products with different review counts
        self.product_no_reviews = Product.objects.create(
            category=self.category,
            name='Product No Reviews',
            description='No reviews',
            price=Decimal('50'),
            stock=10
        )
        
        self.product_few_reviews = Product.objects.create(
            category=self.category,
            name='Product Few Reviews',
            description='Only 2 reviews',
            price=Decimal('60'),
            stock=10
        )
        
        self.product_enough_reviews = Product.objects.create(
            category=self.category,
            name='Product Enough Reviews',
            description='Has 3 reviews',
            price=Decimal('70'),
            stock=10
        )
        
        # Create users
        self.users = [
            User.objects.create_user(username=f'cmduser{i}', password='pass')
            for i in range(5)
        ]
        
        # Add 2 reviews to product_few_reviews
        for i in range(2):
            Review.objects.create(
                product=self.product_few_reviews,
                user=self.users[i],
                rating=4,
                title='Review',
                comment='Comment'
            )
        
        # Add 3 reviews to product_enough_reviews
        for i in range(3):
            Review.objects.create(
                product=self.product_enough_reviews,
                user=self.users[i],
                rating=5,
                title='Review',
                comment='Comment'
            )
    
    @patch('store.review_summary.OpenAI')
    def test_command_skips_products_without_enough_reviews(self, mock_openai):
        """Test command skips products with fewer than 3 reviews"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('generate_review_summaries', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Product No Reviews', output)
        self.assertIn('only 0 reviews', output)
        self.assertIn('Product Few Reviews', output)
        self.assertIn('only 2 reviews', output)
    
    @patch('store.review_summary.OpenAI')
    def test_command_generates_for_eligible_products(self, mock_openai):
        """Test command generates summaries for products with 3+ reviews"""
        from django.core.management import call_command
        from io import StringIO
        
        # Mock OpenAI
        mock_response = {
            "summary": "Great product",
            "pros": ["Pro 1", "Pro 2"],
            "cons": ["Con 1"],
            "sentiment": "positive"
        }
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_client.chat.completions.create.return_value = mock_completion
        
        out = StringIO()
        call_command('generate_review_summaries', stdout=out)
        
        # Verify summary was generated
        self.product_enough_reviews.refresh_from_db()
        self.assertIsNotNone(self.product_enough_reviews.review_summary)
        self.assertEqual(self.product_enough_reviews.review_summary_sentiment, 'positive')


class ReviewSummaryCachingTest(TestCase):
    """Test caching behavior of review summaries"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.product = Product.objects.create(
            category=self.category,
            name='Tablet',
            description='Portable tablet',
            price=Decimal('299.99'),
            stock=20
        )
        self.users = [
            User.objects.create_user(username=f'cacheuser{i}', password='pass')
            for i in range(4)
        ]
        
        # Create reviews
        for i in range(3):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=4,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
    
    def test_summary_cached_for_one_day(self):
        """Test summary is not regenerated within 1 day"""
        # Set recent summary
        recent_time = timezone.now() - timedelta(hours=12)
        self.product.review_summary = 'Cached summary'
        self.product.review_summary_generated_at = recent_time
        self.product.review_summary_review_count = 3
        self.product.save()
        
        should_regen = should_regenerate_summary(self.product)
        self.assertFalse(should_regen)
    
    def test_summary_regenerated_after_one_day(self):
        """Test summary is regenerated after 1 day with new reviews"""
        # Set old summary with 2 reviews
        old_time = timezone.now() - timedelta(days=2)
        self.product.review_summary = 'Old summary'
        self.product.review_summary_generated_at = old_time
        self.product.review_summary_review_count = 2
        self.product.save()
        
        # Now we have 3 reviews (created in setUp), count changed
        should_regen = should_regenerate_summary(self.product)
        self.assertTrue(should_regen)
    
    def test_summary_regenerated_with_new_reviews(self):
        """Test summary regenerated when new reviews are added"""
        # Set summary with 3 reviews
        old_time = timezone.now() - timedelta(days=2)
        self.product.review_summary = 'Old summary'
        self.product.review_summary_generated_at = old_time
        self.product.review_summary_review_count = 3
        self.product.save()
        
        # Add new review
        Review.objects.create(
            product=self.product,
            user=self.users[3],
            rating=5,
            title='New review',
            comment='New comment'
        )
        
        should_regen = should_regenerate_summary(self.product)
        self.assertTrue(should_regen)
    
    def test_summary_not_regenerated_without_new_reviews(self):
        """Test summary not regenerated if old but no new reviews"""
        # Set old summary with 3 reviews
        old_time = timezone.now() - timedelta(days=2)
        self.product.review_summary = 'Old summary'
        self.product.review_summary_generated_at = old_time
        self.product.review_summary_review_count = 3
        self.product.save()
        
        # Don't add new reviews - count should match
        should_regen = should_regenerate_summary(self.product)
        # Should NOT regenerate if no new reviews (even if old)
        # Wait, looking at the logic - it should regenerate if old AND has reviews
        # Let me check the actual implementation
        # Based on review_summary.py, it regenerates if:
        # 1. No summary exists, OR
        # 2. Summary is older than 1 day AND review count has changed
        # So with same count, it won't regenerate
        self.assertFalse(should_regen)
