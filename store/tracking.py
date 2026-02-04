"""
User interaction tracking utilities for SmartShop.
This module provides helper functions to record user interactions across the site.
"""
from .models import UserInteraction


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_session_key(request):
    """Get or create session key for tracking anonymous users"""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def track_interaction(request, interaction_type, **kwargs):
    """
    Track a user interaction.
    
    Args:
        request: Django request object
        interaction_type: Type of interaction (from UserInteraction.INTERACTION_TYPES)
        **kwargs: Additional fields (product, category, order, quantity, search_query, extra_data, etc.)
    
    Returns:
        UserInteraction instance
    """
    # Get user if authenticated
    user = request.user if request.user.is_authenticated else None
    
    # Get session key for anonymous users
    session_key = get_session_key(request) if not user else ''
    
    # Get IP and user agent
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    # Get URLs
    page_url = request.build_absolute_uri()[:500]
    referrer_url = request.META.get('HTTP_REFERER', '')[:500]
    
    # Create interaction record
    interaction = UserInteraction.objects.create(
        user=user,
        session_key=session_key,
        interaction_type=interaction_type,
        ip_address=ip_address,
        user_agent=user_agent,
        page_url=page_url,
        referrer_url=referrer_url,
        **kwargs
    )
    
    return interaction


def track_view_category(request, category):
    """Track category view"""
    return track_interaction(
        request,
        'view_category',
        category=category
    )


def track_view_product(request, product):
    """Track product view"""
    return track_interaction(
        request,
        'view_product',
        product=product,
        category=product.category
    )


def track_add_to_cart(request, product, quantity=1):
    """Track adding product to cart"""
    return track_interaction(
        request,
        'add_to_cart',
        product=product,
        category=product.category,
        quantity=quantity
    )


def track_update_cart(request, product, quantity):
    """Track cart quantity update"""
    return track_interaction(
        request,
        'update_cart',
        product=product,
        category=product.category,
        quantity=quantity
    )


def track_remove_from_cart(request, product):
    """Track removing product from cart"""
    return track_interaction(
        request,
        'remove_from_cart',
        product=product,
        category=product.category
    )


def track_checkout_started(request, cart_items_count=None, cart_total=None):
    """Track checkout process started"""
    extra_data = {}
    if cart_items_count is not None:
        extra_data['cart_items_count'] = cart_items_count
    if cart_total is not None:
        extra_data['cart_total'] = str(cart_total)
    
    return track_interaction(
        request,
        'checkout_started',
        extra_data=extra_data if extra_data else None
    )


def track_order_placed(request, order):
    """Track successful order placement"""
    # Track the main order interaction
    track_interaction(
        request,
        'order_placed',
        order=order,
        extra_data={
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'items_count': order.items.count()
        }
    )
    
    # Also track individual product purchases
    for item in order.items.all():
        track_interaction(
            request,
            'order_placed',
            product=item.product,
            category=item.product.category if item.product else None,
            order=order,
            quantity=item.quantity,
            extra_data={
                'order_number': order.order_number,
                'product_price': str(item.price)
            }
        )


def track_search(request, query, results_count=None):
    """Track search query"""
    extra_data = None
    if results_count is not None:
        extra_data = {'results_count': results_count}
    
    return track_interaction(
        request,
        'search',
        search_query=query,
        extra_data=extra_data
    )


def track_review_submitted(request, product, review):
    """Track review submission"""
    return track_interaction(
        request,
        'review_submitted',
        product=product,
        category=product.category,
        extra_data={
            'rating': review.rating,
            'review_id': review.id
        }
    )
