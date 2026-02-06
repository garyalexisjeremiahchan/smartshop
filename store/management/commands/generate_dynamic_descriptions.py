"""
Management command to generate dynamic descriptions for products

Usage:
    python manage.py generate_dynamic_descriptions [--product-id ID] [--force]
"""

from django.core.management.base import BaseCommand
from store.models import Product
from store.dynamic_description import DynamicDescriptionGenerator


class Command(BaseCommand):
    help = 'Generate AI-powered dynamic product descriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            help='Generate description for a specific product ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if description is fresh',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of products to process',
        )

    def handle(self, *args, **options):
        generator = DynamicDescriptionGenerator()
        
        # Get products to process
        if options['product_id']:
            products = Product.objects.filter(id=options['product_id'], is_active=True)
            if not products.exists():
                self.stdout.write(self.style.ERROR(f'Product with ID {options["product_id"]} not found'))
                return
        else:
            products = Product.objects.filter(is_active=True)
            if options['limit']:
                products = products[:options['limit']]
        
        total = products.count()
        self.stdout.write(f'Processing {total} product(s)...\n')
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, product in enumerate(products, 1):
            self.stdout.write(f'[{i}/{total}] Processing: {product.name}')
            
            try:
                # Check if regeneration is needed
                if not options['force'] and not generator.needs_regeneration(product):
                    self.stdout.write(self.style.WARNING('  ⏭️  Skipped (description is fresh)'))
                    skip_count += 1
                    continue
                
                # Generate description
                updated = generator.update_product_description(product, force=options['force'])
                
                if updated:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Generated description'))
                    self.stdout.write(f'    Preview: {product.dynamic_description[:100]}...\n')
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR('  ✗ Failed to generate'))
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully generated: {success_count}'))
        self.stdout.write(self.style.WARNING(f'⏭️  Skipped: {skip_count}'))
        self.stdout.write(self.style.ERROR(f'✗ Errors: {error_count}'))
        self.stdout.write('='*50)
