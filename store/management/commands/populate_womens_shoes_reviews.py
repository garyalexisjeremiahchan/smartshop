"""
Management command to generate realistic mock reviews for women's shoes products
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Product, Category, Review
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Generate realistic mock reviews for women\'s shoes products'

    # Review templates by sentiment
    REVIEW_TEMPLATES = {
        'positive': {
            5: [
                {
                    'title': 'Perfect fit and super comfortable!',
                    'reasons': ['The fit is absolutely perfect', 'I can wear these all day without any discomfort']
                },
                {
                    'title': 'Best shoes I\'ve ever owned',
                    'reasons': ['The quality is outstanding', 'They go with everything in my wardrobe']
                },
                {
                    'title': 'Absolutely love them!',
                    'reasons': ['So stylish and trendy', 'Super comfortable even after walking for hours']
                },
                {
                    'title': 'Worth every penny',
                    'reasons': ['The craftsmanship is excellent', 'They\'re holding up great after months of wear']
                },
                {
                    'title': 'Highly recommend!',
                    'reasons': ['True to size and very comfortable', 'The color is exactly as shown in the pictures']
                },
                {
                    'title': 'My new favorites',
                    'reasons': ['I get compliments every time I wear them', 'The cushioning is amazing for my feet']
                },
                {
                    'title': 'Exceeded my expectations',
                    'reasons': ['The material feels premium', 'They\'re incredibly lightweight yet supportive']
                },
            ],
            4: [
                {
                    'title': 'Great shoes, very happy',
                    'reasons': ['Comfortable and stylish', 'Good quality for the price']
                },
                {
                    'title': 'Really nice purchase',
                    'reasons': ['They look great with jeans and dresses', 'Arrived quickly and well-packaged']
                },
                {
                    'title': 'Very satisfied',
                    'reasons': ['Comfortable right out of the box', 'The sizing is accurate']
                },
                {
                    'title': 'Good quality shoes',
                    'reasons': ['Nice design and finish', 'They\'re holding up well so far']
                },
                {
                    'title': 'Happy with this purchase',
                    'reasons': ['Comfortable for daily wear', 'The color matches the description perfectly']
                },
            ],
        },
        'neutral': {
            3: [
                {
                    'title': 'Decent shoes, nothing special',
                    'reasons': ['They\'re okay for the price', 'Needed a bit of breaking in']
                },
                {
                    'title': 'Average quality',
                    'reasons': ['Comfortable enough for short periods', 'The material feels a bit cheap']
                },
                {
                    'title': 'It\'s fine',
                    'reasons': ['Does the job but not exceptional', 'Sizing runs slightly small']
                },
                {
                    'title': 'Acceptable purchase',
                    'reasons': ['They look nice but not very comfortable', 'Good for occasional wear']
                },
                {
                    'title': 'Mixed feelings',
                    'reasons': ['Love the style but they\'re a bit stiff', 'Had to order a half size up']
                },
                {
                    'title': 'Could be better',
                    'reasons': ['The design is cute but quality is average', 'They\'re comfortable once broken in']
                },
            ],
        },
        'negative': {
            2: [
                {
                    'title': 'Disappointed with quality',
                    'reasons': ['The material feels cheap', 'They started showing wear after just a few uses']
                },
                {
                    'title': 'Not as expected',
                    'reasons': ['Sizing is way off, had to return', 'The color doesn\'t match the photos']
                },
                {
                    'title': 'Uncomfortable',
                    'reasons': ['They hurt my feet after an hour of wear', 'The arch support is practically non-existent']
                },
                {
                    'title': 'Not worth the price',
                    'reasons': ['Quality doesn\'t match the cost', 'They feel flimsy and poorly made']
                },
                {
                    'title': 'Below average',
                    'reasons': ['The fit is awkward and uncomfortable', 'Already seeing some stitching come loose']
                },
            ],
            1: [
                {
                    'title': 'Terrible quality',
                    'reasons': ['Fell apart after one week', 'Extremely uncomfortable and painful to wear']
                },
                {
                    'title': 'Very disappointed',
                    'reasons': ['Nothing like the pictures', 'Cheapest materials I\'ve ever seen']
                },
                {
                    'title': 'Would not recommend',
                    'reasons': ['Caused blisters on the first wear', 'The sizing is completely wrong']
                },
                {
                    'title': 'Waste of money',
                    'reasons': ['Terrible quality control', 'They look cheap and feel even cheaper']
                },
            ],
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing reviews before generating new ones',
        )

    def handle(self, *args, **options):
        # Get Women's Shoes category
        try:
            womens_shoes = Category.objects.get(name__iexact="Women's Shoes")
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR("Women's Shoes category not found"))
            return

        # Get all products in Women's Shoes category
        products = Product.objects.filter(category=womens_shoes)
        if not products.exists():
            self.stdout.write(self.style.ERROR("No products found in Women's Shoes category"))
            return

        # Get all users
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users found in the database"))
            return

        # Clear existing reviews if flag is set
        if options['clear']:
            deleted_count = Review.objects.filter(product__category=womens_shoes).delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing reviews"))

        total_reviews = 0
        
        for product in products:
            # Randomly decide how many reviews (0-6)
            num_reviews = random.randint(0, 6)
            
            if num_reviews == 0:
                self.stdout.write(f"  {product.name}: 0 reviews (skipped)")
                continue

            # Shuffle users and take only what we need to avoid duplicates
            available_users = random.sample(users, min(num_reviews, len(users)))
            
            reviews_created = 0
            for user in available_users:
                # Check if user already reviewed this product
                if Review.objects.filter(product=product, user=user).exists():
                    continue

                # Randomly select sentiment with weighted probabilities
                # 60% positive, 25% neutral, 15% negative
                sentiment = random.choices(
                    ['positive', 'neutral', 'negative'],
                    weights=[0.60, 0.25, 0.15],
                    k=1
                )[0]

                # Get rating based on sentiment
                if sentiment == 'positive':
                    rating = random.choice([4, 5])
                elif sentiment == 'neutral':
                    rating = 3
                else:  # negative
                    rating = random.choice([1, 2])

                # Get random review template for this rating
                templates = self.REVIEW_TEMPLATES[sentiment][rating]
                template = random.choice(templates)

                # Select 1-2 reasons randomly
                num_reasons = random.randint(1, 2)
                selected_reasons = random.sample(template['reasons'], min(num_reasons, len(template['reasons'])))
                
                # Create comment from reasons
                comment = '. '.join(selected_reasons) + '.'

                # Create review with random date in the past 6 months
                days_ago = random.randint(1, 180)
                created_date = timezone.now() - timedelta(days=days_ago)

                try:
                    review = Review.objects.create(
                        product=product,
                        user=user,
                        rating=rating,
                        title=template['title'],
                        comment=comment,
                        is_approved=True,
                    )
                    # Manually set the created_at date
                    review.created_at = created_date
                    review.save()
                    
                    reviews_created += 1
                    total_reviews += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Error creating review: {str(e)}"))

            self.stdout.write(f"  {product.name}: {reviews_created} reviews created")

        self.stdout.write(self.style.SUCCESS(f"\nTotal reviews created: {total_reviews}"))
