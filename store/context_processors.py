from .models import Cart


def cart_context(request):
    """Add cart information to all templates"""
    cart = None
    cart_items_count = 0
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items_count = cart.total_items
    elif request.session.session_key:
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        cart_items_count = cart.total_items
    
    return {
        'cart': cart,
        'cart_items_count': cart_items_count,
    }
