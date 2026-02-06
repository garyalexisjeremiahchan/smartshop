"""
Management command to generate AI review summaries for products with sufficient reviews
"""
from django.core.management.base import BaseCommand
from store.models import Product, Review
from store.review_summary import generate_review_summary


class Command(BaseCommand):
    help = 'Generate AI-powered review summaries for products with at least 3 reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of summaries even if they already exist',
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Generate summary for a specific product ID only',
        )

    def handle(self, *args, **options):
        force = options['force']
        product_id = options.get('product_id')
        
        # Get products
        if product_id:
            products = Product.objects.filter(id=product_id, is_active=True)
        else:
            products = Product.objects.filter(is_active=True)
        
        total_generated = 0
        total_skipped = 0
        
        for product in products:
            # Get review count
            review_count = Review.objects.filter(
                product=product,
                is_approved=True
            ).count()
            
            # Skip if less than 3 reviews
            if review_count < 3:
                self.stdout.write(f"  {product.name}: Skipped (only {review_count} reviews)")
                total_skipped += 1
                continue
            
            # Skip if summary already exists and not forcing
            if not force and product.review_summary:
                self.stdout.write(f"  {product.name}: Skipped (summary already exists)")
                total_skipped += 1
                continue
            
            # Generate summary
            self.stdout.write(f"  Generating summary for {product.name}...")
            result = generate_review_summary(product)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {product.name}: Summary generated"))
                self.stdout.write(f"    - Sentiment: {result.get('sentiment', 'unknown')}")
                self.stdout.write(f"    - Pros: {len(result.get('pros', []))} points")
                self.stdout.write(f"    - Cons: {len(result.get('cons', []))} points")
                total_generated += 1
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {product.name}: Failed to generate summary"))
                total_skipped += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"Summary Generation Complete"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}"))
        self.stdout.write(f"Total summaries generated: {total_generated}")
        self.stdout.write(f"Total products skipped: {total_skipped}")
