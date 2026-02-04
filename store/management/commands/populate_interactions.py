from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import UserInteraction, Product, Category, Order
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with 300 realistic user interactions'

    def handle(self, *args, **kwargs):
        # Clear existing interactions
        UserInteraction.objects.all().delete()
        
        # Get existing data
        users = list(User.objects.filter(is_superuser=False))
        products = list(Product.objects.all())
        categories = list(Category.objects.all())
        orders = list(Order.objects.all())
        
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Run populate_users first.'))
            return
        
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Run populate_products first.'))
            return
        
        if not categories:
            self.stdout.write(self.style.ERROR('No categories found. Run populate_categories first.'))
            return
        
        # Realistic user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
        ]
        
        # Realistic IP addresses
        def random_ip():
            return f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}'
        
        # Page URLs
        page_urls = [
            'http://localhost:8000/',
            'http://localhost:8000/products/',
            'http://localhost:8000/cart/',
            'http://localhost:8000/checkout/',
        ]
        
        # Referrer URLs
        referrers = [
            'https://www.google.com/',
            'https://www.facebook.com/',
            'https://www.instagram.com/',
            'https://www.twitter.com/',
            '',  # Direct access
        ]
        
        # Search queries
        search_queries = [
            'wireless headphones',
            'laptop',
            'running shoes',
            'coffee maker',
            'smartphone',
            'winter jacket',
            'gaming mouse',
            'organic tea',
            'yoga mat',
            'backpack',
        ]
        
        interactions = []
        created_count = 0
        
        # Generate 300 interactions
        for i in range(300):
            # Random user (80% logged in, 20% anonymous)
            user = random.choice(users) if random.random() > 0.2 else None
            session_key = '' if user else f'session_{random.randint(100000, 999999)}'
            
            # Random timestamp within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Common metadata
            ip_address = random_ip()
            user_agent = random.choice(user_agents)
            page_url = random.choice(page_urls)
            referrer_url = random.choice(referrers)
            
            # Weighted interaction types (more views than purchases)
            interaction_type = random.choices(
                ['view_category', 'view_product', 'add_to_cart', 'update_cart', 
                 'remove_from_cart', 'checkout_started', 'order_placed', 'search', 'review_submitted'],
                weights=[25, 30, 15, 5, 3, 8, 5, 7, 2],
                k=1
            )[0]
            
            # Create interaction based on type
            interaction_data = {
                'user': user,
                'session_key': session_key,
                'interaction_type': interaction_type,
                'timestamp': timestamp,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'page_url': page_url,
                'referrer_url': referrer_url,
            }
            
            if interaction_type == 'view_category':
                category = random.choice(categories)
                interaction_data['category'] = category
                interaction_data['page_url'] = f'http://localhost:8000/category/{category.slug}/'
                
            elif interaction_type == 'view_product':
                product = random.choice(products)
                interaction_data['product'] = product
                interaction_data['category'] = product.category
                interaction_data['page_url'] = f'http://localhost:8000/product/{product.slug}/'
                
            elif interaction_type in ['add_to_cart', 'update_cart']:
                product = random.choice(products)
                interaction_data['product'] = product
                interaction_data['category'] = product.category
                interaction_data['quantity'] = random.randint(1, 5)
                interaction_data['page_url'] = f'http://localhost:8000/product/{product.slug}/'
                
            elif interaction_type == 'remove_from_cart':
                product = random.choice(products)
                interaction_data['product'] = product
                interaction_data['category'] = product.category
                interaction_data['page_url'] = 'http://localhost:8000/cart/'
                
            elif interaction_type == 'checkout_started':
                interaction_data['page_url'] = 'http://localhost:8000/checkout/'
                interaction_data['extra_data'] = {
                    'cart_items_count': random.randint(1, 8),
                    'cart_total': round(random.uniform(20, 500), 2)
                }
                
            elif interaction_type == 'order_placed':
                if orders and user:
                    order = random.choice(orders)
                    interaction_data['order'] = order
                    interaction_data['user'] = order.user
                    interaction_data['page_url'] = 'http://localhost:8000/checkout/'
                    interaction_data['extra_data'] = {
                        'order_total': float(order.total_amount),
                        'items_count': order.items.count()
                    }
                else:
                    # Skip if no orders or no user
                    continue
                    
            elif interaction_type == 'search':
                query = random.choice(search_queries)
                interaction_data['search_query'] = query
                interaction_data['page_url'] = f'http://localhost:8000/products/?search={query}'
                interaction_data['extra_data'] = {
                    'results_count': random.randint(0, 50)
                }
                
            elif interaction_type == 'review_submitted':
                if user:  # Only logged-in users can submit reviews
                    product = random.choice(products)
                    interaction_data['product'] = product
                    interaction_data['category'] = product.category
                    interaction_data['user'] = user
                    interaction_data['page_url'] = f'http://localhost:8000/product/{product.slug}/'
                    interaction_data['extra_data'] = {
                        'rating': random.randint(3, 5)
                    }
                else:
                    # Skip if no user
                    continue
            
            interaction = UserInteraction.objects.create(**interaction_data)
            created_count += 1
            
            if created_count % 50 == 0:
                self.stdout.write(f'Created {created_count} interactions...')
        
        # Statistics
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} user interactions'))
        
        # Show breakdown by type
        for interaction_type in UserInteraction.INTERACTION_TYPES:
            count = UserInteraction.objects.filter(interaction_type=interaction_type[0]).count()
            if count > 0:
                self.stdout.write(f'  {interaction_type[1]}: {count}')
        
        # Show user breakdown
        logged_in = UserInteraction.objects.filter(user__isnull=False).count()
        anonymous = UserInteraction.objects.filter(user__isnull=True).count()
        self.stdout.write(f'\nLogged-in users: {logged_in}')
        self.stdout.write(f'Anonymous users: {anonymous}')
