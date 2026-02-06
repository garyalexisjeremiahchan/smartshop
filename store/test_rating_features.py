"""
Unit tests for Product Rating and Review Features

Tests cover:
- Star rating template tag
- Username masking filter
- Review form with star symbols
- Average rating calculation
- Rating display and rounding
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.template import Context, Template
from decimal import Decimal
from store.models import Category, Product, Review
from store.forms import ReviewForm
from store.templatetags.star_ratings import star_rating, mask_username


class StarRatingTemplateTagTest(TestCase):
    """Test the star_rating template tag functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            stock=10
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_star_rating_with_perfect_score(self):
        """Test star rating displays 5 filled stars for 5.0 rating"""
        # Create review with 5 stars
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Perfect',
            comment='Excellent product'
        )
        
        result = star_rating(5.0, show_number=False)
        self.assertEqual(len(result['full_stars']), 5)
        self.assertFalse(result['half_star'])
        self.assertEqual(len(result['empty_stars']), 0)
    
    def test_star_rating_with_half_star(self):
        """Test star rating displays half star for 3.5 rating"""
        result = star_rating(3.5, show_number=False)
        self.assertEqual(len(result['full_stars']), 3)
        self.assertTrue(result['half_star'])
        self.assertEqual(len(result['empty_stars']), 1)
    
    def test_star_rating_rounds_to_nearest_half(self):
        """Test star rating rounds to nearest 0.5"""
        # 3.3 should round to 3.5
        result = star_rating(3.3, show_number=False)
        self.assertEqual(len(result['full_stars']), 3)
        self.assertTrue(result['half_star'])
        
        # 3.7 should round to 3.5
        result2 = star_rating(3.7, show_number=False)
        self.assertEqual(len(result2['full_stars']), 3)
        self.assertTrue(result2['half_star'])
        
        # 3.8 should round to 4.0
        result3 = star_rating(3.8, show_number=False)
        self.assertEqual(len(result3['full_stars']), 4)
        self.assertFalse(result3['half_star'])
    
    def test_star_rating_with_show_number(self):
        """Test star rating includes numeric value when requested"""
        result = star_rating(4.2, show_number=True)
        self.assertTrue(result['show_number'])
        self.assertEqual(result['rating'], 4.2)
    
    def test_star_rating_zero_rating(self):
        """Test star rating with 0 rating shows empty stars"""
        result = star_rating(0, show_number=False)
        self.assertEqual(len(result['full_stars']), 0)
        self.assertFalse(result['half_star'])
        self.assertEqual(len(result['empty_stars']), 5)


class MaskUsernameFilterTest(TestCase):
    """Test username masking filter functionality"""
    
    def test_mask_username_standard(self):
        """Test masking of standard username"""
        result = mask_username('admin')
        self.assertEqual(result, 'a***n')
        self.assertEqual(len(result), 5)
    
    def test_mask_username_long(self):
        """Test masking of longer username"""
        result = mask_username('testuser123')
        self.assertEqual(result, 't*********3')
        self.assertTrue(result.startswith('t'))
        self.assertTrue(result.endswith('3'))
    
    def test_mask_username_short(self):
        """Test masking preserves short usernames"""
        result = mask_username('ab')
        self.assertEqual(result, 'ab')  # Too short to mask
    
    def test_mask_username_single_char(self):
        """Test masking preserves single character"""
        result = mask_username('a')
        self.assertEqual(result, 'a')
    
    def test_mask_username_empty(self):
        """Test masking handles empty string"""
        result = mask_username('')
        self.assertEqual(result, '')
    
    def test_mask_username_none(self):
        """Test masking handles None"""
        result = mask_username(None)
        self.assertIsNone(result)


class ReviewFormStarsTest(TestCase):
    """Test review form with star symbols instead of text"""
    
    def test_review_form_has_star_choices(self):
        """Test form displays star symbols for rating choices"""
        form = ReviewForm()
        choices = form.fields['rating'].widget.choices
        
        # Check that choices use star symbols
        choice_dict = dict(choices)
        self.assertEqual(choice_dict[5], '★★★★★')
        self.assertEqual(choice_dict[4], '★★★★☆')
        self.assertEqual(choice_dict[3], '★★★☆☆')
        self.assertEqual(choice_dict[2], '★★☆☆☆')
        self.assertEqual(choice_dict[1], '★☆☆☆☆')
    
    def test_review_form_default_rating(self):
        """Test form defaults to 5 stars"""
        form = ReviewForm()
        self.assertEqual(form.fields['rating'].initial, 5)
    
    def test_review_form_valid_with_stars(self):
        """Test form validates correctly with star rating"""
        form_data = {
            'rating': 5,
            'title': 'Great product',
            'comment': 'Very satisfied with this purchase.'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_preserves_rating_on_edit(self):
        """Test existing review rating is preserved"""
        user = User.objects.create_user(username='user1', password='pass')
        category = Category.objects.create(name='Cat', slug='cat')
        product = Product.objects.create(
            category=category,
            name='Product',
            description='Desc',
            price=Decimal('50'),
            stock=5
        )
        review = Review.objects.create(
            product=product,
            user=user,
            rating=3,
            title='Okay',
            comment='It was okay'
        )
        
        form = ReviewForm(instance=review)
        # When editing, should not reset to default
        self.assertNotEqual(form.fields['rating'].initial, 5)


class AverageRatingCalculationTest(TestCase):
    """Test average rating calculation and display"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            description='Gaming laptop',
            price=Decimal('999.99'),
            stock=5
        )
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                password='pass123'
            )
            self.users.append(user)
    
    def test_average_rating_single_review(self):
        """Test average with single review"""
        Review.objects.create(
            product=self.product,
            user=self.users[0],
            rating=4,
            title='Good',
            comment='Good product'
        )
        self.assertEqual(self.product.average_rating, 4.0)
    
    def test_average_rating_multiple_reviews(self):
        """Test average calculation with multiple reviews"""
        ratings = [5, 4, 5, 3, 4]
        for i, rating in enumerate(ratings):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=rating,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        # Average: (5+4+5+3+4)/5 = 21/5 = 4.2
        self.assertEqual(self.product.average_rating, 4.2)
    
    def test_average_rating_rounds_to_one_decimal(self):
        """Test average rating is rounded to 1 decimal place"""
        ratings = [5, 5, 3]
        for i, rating in enumerate(ratings):
            Review.objects.create(
                product=self.product,
                user=self.users[i],
                rating=rating,
                title=f'Review {i}',
                comment=f'Comment {i}'
            )
        
        # Average: (5+5+3)/3 = 13/3 = 4.333... → 4.3
        self.assertEqual(self.product.average_rating, 4.3)
    
    def test_average_rating_no_reviews(self):
        """Test product with no reviews returns 0"""
        self.assertEqual(self.product.average_rating, 0)
    
    def test_review_count_property(self):
        """Test review_count property returns correct count"""
        Review.objects.create(
            product=self.product,
            user=self.users[0],
            rating=5,
            title='Great',
            comment='Excellent'
        )
        Review.objects.create(
            product=self.product,
            user=self.users[1],
            rating=4,
            title='Good',
            comment='Nice'
        )
        
        self.assertEqual(self.product.review_count, 2)


class RatingDisplayIntegrationTest(TestCase):
    """Integration tests for rating display on product pages"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        self.product = Product.objects.create(
            category=self.category,
            name='Running Shoes',
            description='Comfortable shoes',
            price=Decimal('79.99'),
            stock=10
        )
        self.user = User.objects.create_user(
            username='reviewer',
            password='pass123'
        )
    
    def test_product_detail_shows_average_rating(self):
        """Test product detail page displays average rating"""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title='Perfect',
            comment='Love these shoes'
        )
        
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '5.0')  # Rating displayed
    
    def test_review_display_masks_username(self):
        """Test review displays masked username"""
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Good',
            comment='Nice shoes'
        )
        
        response = self.client.get(f'/product/{self.product.slug}/')
        self.assertContains(response, 'r******r')  # Masked username
        self.assertNotContains(response, 'reviewer')  # Full username not shown
    
    def test_product_with_no_rating_shows_no_stars(self):
        """Test product without reviews doesn't show rating"""
        response = self.client.get(f'/product/{self.product.slug}/')
        # Check that rating section is not displayed
        content = response.content.decode()
        # Average rating section should be hidden when average_rating is 0
        self.assertNotIn('bi-star-fill', content)  # No filled stars
