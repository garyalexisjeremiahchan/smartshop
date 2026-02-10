"""
Tool implementations for the shopping assistant.
These functions execute database queries and return structured data for the AI.
"""

from django.db.models import Q, Avg, Count, F
from django.core.cache import cache
from django.utils import timezone
from store.models import Product, Category, Review, ProductImage, Cart, CartItem
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def search_products(query=None, category=None, min_price=None, max_price=None, 
                   min_rating=None, in_stock_only=False, sort='popular', limit=5):
    """
    Search for products with various filters and sorting options.
    
    Returns: List of product dictionaries with essential information
    """
    try:
        # Start with active products
        products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
        
        # Apply text search
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(specifications__icontains=query)
            )
        
        # Apply category filter
        if category:
            products = products.filter(category__slug=category)
        
        # Apply price filters
        if min_price is not None:
            products = products.filter(price__gte=Decimal(str(min_price)))
        if max_price is not None:
            products = products.filter(price__lte=Decimal(str(max_price)))
        
        # Apply stock filter
        if in_stock_only:
            products = products.filter(stock__gt=0)
        
        # Annotate with average rating
        products = products.annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply rating filter
        if min_rating is not None:
            products = products.filter(avg_rating__gte=min_rating)
        
        # Apply sorting
        if sort == 'popular':
            products = products.order_by('-units_sold', '-avg_rating')
        elif sort == 'latest':
            products = products.order_by('-created_at')
        elif sort == 'price_low_high':
            products = products.order_by('price')
        elif sort == 'price_high_low':
            products = products.order_by('-price')
        elif sort == 'rating':
            products = products.order_by('-avg_rating', '-approved_reviews')
        
        # Limit results (max 10)
        limit = min(int(limit), 10)
        products = products[:limit]
        
        # Format results
        results = []
        for product in products:
            primary_image = product.images.filter(is_primary=True).first() or product.images.first()
            
            # Determine stock status
            if product.stock == 0:
                stock_status = 'out_of_stock'
            elif product.stock <= 5:
                stock_status = 'low_stock'
            else:
                stock_status = 'in_stock'
            
            results.append({
                'id': product.id,
                'title': product.name,
                'price': float(product.price),
                'currency': 'SGD',
                'image_url': primary_image.image.url if primary_image else '',
                'rating': float(product.avg_rating) if product.avg_rating else 0,
                'review_count': product.approved_reviews,
                'stock_status': stock_status,
                'stock_quantity': product.stock,
                'url': f'/product/{product.slug}/',
                'category': product.category.name,
                'short_description': product.description[:150] + '...' if len(product.description) > 150 else product.description
            })
        
        return {
            'success': True,
            'products': results,
            'total_found': len(results)
        }
    
    except Exception as e:
        logger.error(f"Error in search_products: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to search products',
            'products': []
        }


def get_product_details(product_id):
    """
    Get comprehensive details for a specific product.
    
    Returns: Detailed product information
    """
    try:
        cache_key = f'product_details_{product_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        product = Product.objects.select_related('category').prefetch_related(
            'images', 'reviews'
        ).annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        ).get(id=product_id, is_active=True)
        
        # Get all images
        images = [
            {
                'url': img.image.url,
                'alt_text': img.alt_text or product.name,
                'is_primary': img.is_primary
            }
            for img in product.images.all()
        ]
        
        # Determine stock status
        if product.stock == 0:
            stock_status = 'out_of_stock'
        elif product.stock <= 5:
            stock_status = 'low_stock'
        else:
            stock_status = 'in_stock'
        
        result = {
            'success': True,
            'product': {
                'id': product.id,
                'title': product.name,
                'description': product.description,
                'price': float(product.price),
                'currency': 'SGD',
                'category': product.category.name,
                'category_slug': product.category.slug,
                'stock': product.stock,
                'stock_status': stock_status,
                'rating': float(product.avg_rating) if product.avg_rating else 0,
                'review_count': product.approved_reviews,
                'units_sold': product.units_sold,
                'images': images,
                'url': f'/product/{product.slug}/',
                'created_at': product.created_at.isoformat(),
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        
        return result
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'error': 'Product not found'
        }
    except Exception as e:
        logger.error(f"Error in get_product_details: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to get product details'
        }


def get_product_specs(product_id):
    """
    Get product specifications in structured format.
    
    Returns: Specifications as key-value pairs
    """
    try:
        cache_key = f'product_specs_{product_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Parse specifications (assuming they're in a structured format)
        # This can be adapted based on how specs are stored
        specs = []
        if product.specifications:
            # Simple parsing - assuming line-based format like "Key: Value"
            for line in product.specifications.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    specs.append({
                        'key': key.strip(),
                        'value': value.strip()
                    })
                elif line:
                    # Single line without colon
                    specs.append({
                        'key': 'Feature',
                        'value': line
                    })
        
        result = {
            'success': True,
            'id': product.id,
            'product_name': product.name,
            'specifications': specs,
            'has_specifications': bool(specs)
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, result, 600)
        
        return result
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'error': 'Product not found'
        }
    except Exception as e:
        logger.error(f"Error in get_product_specs: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to get product specifications'
        }


def get_availability(product_id):
    """
    Check product availability and stock status.
    
    Returns: Current stock information
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Determine availability status
        if product.stock == 0:
            status = 'out_of_stock'
            message = 'Currently out of stock'
        elif product.stock <= 5:
            status = 'low_stock'
            message = f'Only {product.stock} left in stock'
        else:
            status = 'in_stock'
            message = 'In stock'
        
        return {
            'success': True,
            'id': product.id,
            'product_name': product.name,
            'stock_quantity': product.stock,
            'status': status,
            'message': message,
            'is_available': product.stock > 0
        }
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'error': 'Product not found'
        }
    except Exception as e:
        logger.error(f"Error in get_availability: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to check availability'
        }


def get_reviews_summary(product_id):
    """
    Get summary of customer reviews including ratings, pros/cons, and sentiment.
    Uses precomputed summaries if available, otherwise generates basic summary.
    
    Returns: Review summary with statistics and key points
    """
    try:
        product = Product.objects.prefetch_related('reviews').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        ).get(id=product_id, is_active=True)
        
        # Use precomputed summary if available and recent
        if product.review_summary and product.review_summary_generated_at:
            # Check if summary is less than 7 days old
            days_old = (timezone.now() - product.review_summary_generated_at).days
            if days_old < 7:
                return {
                    'success': True,
                    'id': product.id,
                    'product_name': product.name,
                    'average_rating': float(product.avg_rating) if product.avg_rating else 0,
                    'review_count': product.approved_reviews,
                    'summary': product.review_summary,
                    'pros': product.review_summary_pros.split('\n') if product.review_summary_pros else [],
                    'cons': product.review_summary_cons.split('\n') if product.review_summary_cons else [],
                    'sentiment': product.review_summary_sentiment or 'neutral',
                    'summary_generated_at': product.review_summary_generated_at.isoformat()
                }
        
        # Generate basic summary from recent reviews
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')[:10]
        
        if not reviews.exists():
            return {
                'success': True,
                'id': product.id,
                'product_name': product.name,
                'average_rating': 0,
                'review_count': 0,
                'message': 'No reviews yet for this product'
            }
        
        # Calculate rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[f'{i}_star'] = reviews.filter(rating=i).count()
        
        # Get sample review highlights
        recent_reviews = [
            {
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment[:100] + '...' if len(review.comment) > 100 else review.comment,
                'created_at': review.created_at.isoformat()
            }
            for review in reviews[:5]
        ]
        
        return {
            'success': True,
            'id': product.id,
            'product_name': product.name,
            'average_rating': float(product.avg_rating) if product.avg_rating else 0,
            'review_count': product.review_count,
            'rating_distribution': rating_dist,
            'recent_reviews': recent_reviews,
            'message': f'Based on {product.review_count} customer reviews'
        }
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'error': 'Product not found'
        }
    except Exception as e:
        logger.error(f"Error in get_reviews_summary: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to get review summary'
        }


def get_similar_products(product_id, limit=3):
    """
    Find similar products based on category and attributes.
    
    Returns: List of similar products
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Find products in the same category, excluding the current product
        similar = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(
            id=product_id
        ).select_related('category').prefetch_related('images').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Prefer products with similar price range
        price_lower = product.price * Decimal('0.7')
        price_upper = product.price * Decimal('1.3')
        similar = similar.filter(price__gte=price_lower, price__lte=price_upper)
        
        # Order by rating and popularity
        similar = similar.order_by('-avg_rating', '-units_sold')[:min(int(limit), 5)]
        
        results = []
        for p in similar:
            primary_image = p.images.filter(is_primary=True).first() or p.images.first()
            
            if p.stock == 0:
                stock_status = 'out_of_stock'
            elif p.stock <= 5:
                stock_status = 'low_stock'
            else:
                stock_status = 'in_stock'
            
            results.append({
                'product_id': p.id,
                'title': p.name,
                'price': float(p.price),
                'currency': 'SGD',
                'image_url': primary_image.image.url if primary_image else '',
                'rating': float(p.avg_rating) if p.avg_rating else 0,
                'review_count': p.approved_reviews,
                'stock_status': stock_status,
                'url': f'/product/{p.slug}/',
                'category': p.category.name
            })
        
        return {
            'success': True,
            'original_product': product.name,
            'similar_products': results,
            'total_found': len(results)
        }
    
    except Product.DoesNotExist:
        return {
            'success': False,
            'error': 'Product not found'
        }
    except Exception as e:
        logger.error(f"Error in get_similar_products: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to find similar products'
        }


def get_categories():
    """
    Get all active product categories.
    
    Returns: List of categories with product counts and navigation URL
    """
    try:
        categories = Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('name')
        
        results = [
            {
                'name': cat.name,
                'slug': cat.slug,
                'product_count': cat.product_count,
                'description': cat.description,
                'url': f'/category/{cat.slug}/'
            }
            for cat in categories
        ]
        
        return {
            'success': True,
            'categories': results,
            'total_categories': len(results),
            'category_page_url': '/categories/',
            'message': 'You can browse all categories on our category page'
        }
    
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to get categories'
        }


def get_top_selling_products(limit=10):
    """
    Get top selling products based on units sold.
    
    Returns: List of best-selling products
    """
    try:
        # Get products sorted by units_sold
        products = Product.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('images').annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
        ).order_by('-units_sold', '-avg_rating')[:min(int(limit), 10)]
        
        # Format results
        results = []
        for product in products:
            primary_image = product.images.filter(is_primary=True).first() or product.images.first()
            
            # Determine stock status
            if product.stock == 0:
                stock_status = 'out_of_stock'
            elif product.stock <= 5:
                stock_status = 'low_stock'
            else:
                stock_status = 'in_stock'
            
            results.append({
                'id': product.id,
                'title': product.name,
                'price': float(product.price),
                'currency': 'SGD',
                'image_url': primary_image.image.url if primary_image else '',
                'rating': float(product.avg_rating) if product.avg_rating else 0,
                'review_count': product.approved_reviews,
                'stock_status': stock_status,
                'stock_quantity': product.stock,
                'url': f'/product/{product.slug}/',
                'category': product.category.name,
                'units_sold': product.units_sold,
                'short_description': product.description[:150] + '...' if len(product.description) > 150 else product.description
            })
        
        return {
            'success': True,
            'products': results,
            'total_found': len(results),
            'message': f'These are our top {len(results)} best-selling products'
        }
    
    except Exception as e:
        logger.error(f"Error in get_top_selling_products: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to get top selling products',
            'products': []
        }


def add_to_cart(product_id, quantity=1, request=None):
    """
    Add a product to the shopping cart.
    
    Args:
        product_id: ID of the product to add
        quantity: Number of items to add (default: 1)
        request: Django request object (required for cart session/user)
    
    Returns: Cart update confirmation with updated cart details
    """
    logger.info(f"add_to_cart called: product_id={product_id}, quantity={quantity}, request={request}")
    
    if not request:
        logger.error("add_to_cart: No request object provided")
        return {
            'success': False,
            'error': 'Request context required for cart operations'
        }
    
    try:
        # Validate product
        logger.info(f"Looking up product with id={product_id}, is_active=True")
        product = Product.objects.get(id=product_id, is_active=True)
        logger.info(f"Product found: {product.name}, stock={product.stock}")
        logger.info(f"Product found: {product.name}, stock={product.stock}")
        
        # Validate quantity
        quantity = int(quantity)
        logger.info(f"Quantity validated: {quantity}")
        if quantity < 1:
            logger.error(f"Invalid quantity: {quantity}")
            return {
                'success': False,
                'error': 'Quantity must be at least 1'
            }
        
        if quantity > product.stock:
            logger.error(f"Insufficient stock: requested={quantity}, available={product.stock}")
            return {
                'success': False,
                'error': f'Only {product.stock} items available in stock',
                'available_stock': product.stock
            }
        
        # Get or create cart
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            logger.info(f"Cart for user {request.user.username}: created={created}, cart_id={cart.id}")
        else:
            if not request.session.session_key:
                request.session.create()
                logger.info(f"Created new session: {request.session.session_key}")
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
            logger.info(f"Cart for session {request.session.session_key}: created={created}, cart_id={cart.id}")
            logger.info(f"Cart for session {request.session.session_key}: created={created}, cart_id={cart.id}")
        
        # Add or update cart item
        logger.info(f"Getting or creating CartItem for cart={cart.id}, product={product.id}")
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        logger.info(f"CartItem: item_created={item_created}, id={cart_item.id}")
        
        old_quantity = 0 if item_created else cart_item.quantity
        logger.info(f"Old quantity: {old_quantity}")
        
        if not item_created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                cart_item.quantity = product.stock
                quantity_added = product.stock - old_quantity
            else:
                quantity_added = quantity
        else:
            cart_item.quantity = quantity
            quantity_added = quantity
        
        logger.info(f"New cart_item.quantity={cart_item.quantity}, quantity_added={quantity_added}")
        cart_item.save()
        logger.info("CartItem saved successfully")
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        logger.info(f"Cart refreshed: total_items={cart.total_items}, total_price={cart.total_price}")
        
        result = {
            'success': True,
            'message': f'Added {quantity_added}x {product.name} to cart',
            'product': {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity_added': quantity_added
            },
            'cart': {
                'total_items': cart.total_items,
                'total_price': float(cart.total_price),
                'cart_url': '/cart/'
            }
        }
        logger.info(f"add_to_cart returning success: {result}")
        return result
    
    except Product.DoesNotExist:
        logger.error(f"Product.DoesNotExist: product_id={product_id}")
        return {
            'success': False,
            'error': 'Product not found or not available'
        }
    except ValueError as e:
        logger.error(f"ValueError in add_to_cart: {str(e)}")
        return {
            'success': False,
            'error': 'Invalid quantity value'
        }
    except Exception as e:
        logger.error(f"Unexpected error in add_to_cart: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': 'Failed to add product to cart'
        }
