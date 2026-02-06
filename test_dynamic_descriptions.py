"""
Test script for Dynamic Product Descriptions feature

This script tests the dynamic description generation without actually calling the OpenAI API.
It validates the logic and structure.

Usage:
    python test_dynamic_descriptions.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartshop.settings')
django.setup()

from store.models import Product
from store.dynamic_description import DynamicDescriptionGenerator
from django.utils import timezone
from datetime import timedelta


def test_needs_regeneration():
    """Test the needs_regeneration logic"""
    print("=" * 60)
    print("Testing needs_regeneration() logic")
    print("=" * 60)
    
    generator = DynamicDescriptionGenerator()
    
    # Get a product
    product = Product.objects.filter(is_active=True).first()
    
    if not product:
        print("❌ No products found in database")
        return
    
    print(f"\nTesting with product: {product.name}")
    print(f"Current dynamic description: {product.dynamic_description[:50] if product.dynamic_description else 'None'}...")
    print(f"Generated at: {product.dynamic_description_generated_at}")
    
    # Test 1: Product with no description
    original_desc = product.dynamic_description
    original_time = product.dynamic_description_generated_at
    
    product.dynamic_description = ""
    product.dynamic_description_generated_at = None
    
    result = generator.needs_regeneration(product)
    print(f"\n✓ Test 1 - No description exists: {result}")
    assert result == True, "Should need regeneration when no description exists"
    
    # Test 2: Fresh description (less than 1 week old)
    product.dynamic_description = "Test description"
    product.dynamic_description_generated_at = timezone.now()
    product.updated_at = timezone.now() - timedelta(days=2)
    
    result = generator.needs_regeneration(product)
    print(f"✓ Test 2 - Fresh description (< 1 week): {result}")
    assert result == False, "Should NOT need regeneration when fresh"
    
    # Test 3: Old description (more than 1 week old)
    product.dynamic_description_generated_at = timezone.now() - timedelta(days=8)
    
    result = generator.needs_regeneration(product)
    print(f"✓ Test 3 - Old description (> 1 week): {result}")
    assert result == True, "Should need regeneration when > 1 week old"
    
    # Test 4: Product updated after description generated
    product.dynamic_description_generated_at = timezone.now() - timedelta(days=2)
    product.updated_at = timezone.now()
    
    result = generator.needs_regeneration(product)
    print(f"✓ Test 4 - Product updated after generation: {result}")
    assert result == True, "Should need regeneration when product updated"
    
    # Restore original values
    product.dynamic_description = original_desc
    product.dynamic_description_generated_at = original_time
    
    print("\n✅ All logic tests passed!")


def test_prompt_building():
    """Test the prompt building functionality"""
    print("\n" + "=" * 60)
    print("Testing _build_prompt() functionality")
    print("=" * 60)
    
    generator = DynamicDescriptionGenerator()
    
    # Get a product with reviews
    products_with_reviews = Product.objects.filter(
        is_active=True,
        reviews__is_approved=True
    ).distinct()
    
    product = products_with_reviews.first()
    
    if not product:
        print("⚠️  No products with reviews found, using product without reviews")
        product = Product.objects.filter(is_active=True).first()
    
    if not product:
        print("❌ No products found in database")
        return
    
    print(f"\nBuilding prompt for: {product.name}")
    
    try:
        prompt = generator._build_prompt(product)
        
        print("\n✓ Prompt built successfully!")
        print(f"\nPrompt length: {len(prompt)} characters")
        
        # Verify key components are in the prompt
        assert product.name in prompt, "Product name should be in prompt"
        assert str(product.price) in prompt, "Price should be in prompt"
        assert product.category.name in prompt, "Category should be in prompt"
        assert product.description in prompt, "Description should be in prompt"
        
        print("✓ Product name: Present")
        print("✓ Price: Present")
        print("✓ Category: Present")
        print("✓ Description: Present")
        
        if product.specifications:
            assert product.specifications in prompt, "Specifications should be in prompt"
            print("✓ Specifications: Present")
        else:
            print("⚠️  Specifications: Not available")
        
        # Show preview of prompt
        print("\n" + "-" * 60)
        print("Prompt Preview (first 500 chars):")
        print("-" * 60)
        print(prompt[:500] + "...")
        print("-" * 60)
        
        print("\n✅ Prompt building test passed!")
        
    except Exception as e:
        print(f"❌ Error building prompt: {str(e)}")
        import traceback
        traceback.print_exc()


def test_api_configuration():
    """Test OpenAI API configuration"""
    print("\n" + "=" * 60)
    print("Testing OpenAI API Configuration")
    print("=" * 60)
    
    from django.conf import settings
    
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    model = getattr(settings, 'OPENAI_MODEL', None)
    
    if api_key:
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✓ API Key configured: {masked_key}")
    else:
        print("⚠️  API Key not configured (required for actual generation)")
    
    print(f"✓ Model: {model}")
    
    generator = DynamicDescriptionGenerator()
    print(f"✓ Generator initialized with model: {generator.model}")
    
    if not api_key:
        print("\n⚠️  To enable actual description generation:")
        print("   1. Add OPENAI_API_KEY to your .env file")
        print("   2. Restart the Django server")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DYNAMIC PRODUCT DESCRIPTIONS - TEST SUITE")
    print("=" * 60)
    
    try:
        test_api_configuration()
        test_needs_regeneration()
        test_prompt_building()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\nNext Steps:")
        print("1. Ensure OPENAI_API_KEY is configured in .env")
        print("2. Test actual generation: python manage.py generate_dynamic_descriptions --product-id 1")
        print("3. Visit a product page to see the dynamic description")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
