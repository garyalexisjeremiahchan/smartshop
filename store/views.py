from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from .models import Category, Product, ProductImage, Review, Cart, CartItem, Order, OrderItem
from .forms import ReviewForm, CheckoutForm
from .tracking import (
    track_view_category, track_view_product, track_add_to_cart,
    track_update_cart, track_remove_from_cart, track_checkout_started,
    track_order_placed, track_search, track_review_submitted
)
from .recommendations import get_ai_recommended_products
from .ai_search import get_ai_search_results, get_autocomplete_suggestions, get_trending_searches
from .review_summary import generate_review_summary, should_regenerate_summary
from .dynamic_description import DynamicDescriptionGenerator


def home(request):
    """Home page view displaying categories"""
    categories = Category.objects.filter(is_active=True)
    featured_products = Product.objects.filter(is_active=True).order_by('-units_sold')[:8]
    
    # Get AI-powered recommended products with caching (1 hour)
    # User-specific cache key
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    cache_key = f'ai_recommended_products_{user_id}'
    recommended_products_with_scores = cache.get(cache_key)
    
    if recommended_products_with_scores is None:
        # Cache miss - call AI API with user context
        recommended_products_with_scores = get_ai_recommended_products(user=request.user, limit=8)
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, recommended_products_with_scores, 3600)
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'recommended_products': recommended_products_with_scores,
    }
    return render(request, 'store/home.html', context)


def category_list(request, slug=None):
    """Category page with product filtering and sorting"""
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    current_category = None
    
    # Filter by category
    if slug:
        current_category = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=current_category)
        # Track category view
        track_view_category(request, current_category)
    
    # AI-powered search functionality
    search_query = request.GET.get('search', '')
    ai_results = []
    if search_query:
        # Use AI-powered search with caching
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        cache_key = f'ai_search_{user_id}_{search_query[:50]}'
        ai_results = cache.get(cache_key)
        
        if ai_results is None:
            # Cache miss - call AI search
            ai_results = get_ai_search_results(search_query, user=request.user, limit=50)
            # Cache for 30 minutes
            cache.set(cache_key, ai_results, 1800)
        
        # Extract product IDs from AI results
        if ai_results:
            product_ids = [product.id for product, score, reason in ai_results]
            # Preserve AI ranking order
            products = Product.objects.filter(id__in=product_ids, is_active=True)
            # Create a dictionary to maintain order
            products_dict = {p.id: p for p in products}
            products = [products_dict[pid] for pid in product_ids if pid in products_dict]
        else:
            products = []
        
        # Track search
        track_search(request, search_query, results_count=len(products))
    
    # Sorting (only apply if not using AI search results)
    sort_by = request.GET.get('sort', 'latest')
    if not search_query:
        # Only sort when not searching (AI already ranks by relevance)
        if sort_by == 'popular':
            products = products.order_by('-units_sold')
        elif sort_by == 'latest':
            products = products.order_by('-created_at')
        elif sort_by == 'top_sales':
            products = products.order_by('-units_sold')
        elif sort_by == 'price_low_high':
            products = products.order_by('price')
        elif sort_by == 'price_high_low':
            products = products.order_by('-price')
    
    context = {
        'categories': categories,
        'products': products,
        'current_category': current_category,
        'sort_by': sort_by,
        'search_query': search_query,
        'ai_results': ai_results if search_query else [],
    }
    return render(request, 'store/category_list.html', context)


def product_detail(request, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Track product view
    track_view_product(request, product)
    
    # Generate or update AI review summary if needed
    if should_regenerate_summary(product):
        generate_review_summary(product)
        # Refresh product instance to get updated summary
        product.refresh_from_db()
    
    # Generate or update dynamic product description if needed
    description_generator = DynamicDescriptionGenerator()
    if description_generator.needs_regeneration(product):
        description_generator.update_product_description(product)
        # Refresh product instance to get updated description
        product.refresh_from_db()
    
    # Check if user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    # Handle review form submission
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            try:
                review.save()
                # Track review submission
                track_review_submitted(request, product, review)
                messages.success(request, 'Your review has been submitted successfully!')
                return redirect('store:product_detail', slug=slug)
            except:
                messages.error(request, 'You have already reviewed this product.')
    else:
        form = ReviewForm()
    
    # Prepare review summary data for template
    has_summary = (
        product.review_summary and 
        reviews.count() >= 3
    )
    
    context = {
        'product': product,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'has_summary': has_summary,
    }
    return render(request, 'store/product_detail.html', context)


def get_or_create_cart(request):
    """Helper function to get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        messages.error(request, 'Invalid quantity.')
        return redirect('store:product_detail', slug=product.slug)
    
    if quantity > product.stock:
        messages.error(request, f'Only {product.stock} items available in stock.')
        return redirect('store:product_detail', slug=product.slug)
    
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            messages.warning(request, f'Maximum stock reached. Only {product.stock} items available.')
    else:
        cart_item.quantity = quantity
    
    cart_item.save()
    
    # Track add to cart
    track_add_to_cart(request, product, quantity)
    
    messages.success(request, f'{product.name} added to cart!')
    
    return redirect(request.META.get('HTTP_REFERER', 'store:cart'))


def cart_view(request):
    """Shopping cart view"""
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    elif request.session.session_key:
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    
    context = {
        'cart': cart,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify the cart item belongs to the current user/session
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'Invalid cart item.')
            return redirect('store:cart')
    else:
        if cart_item.cart.session_key != request.session.session_key:
            messages.error(request, 'Invalid cart item.')
            return redirect('store:cart')
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        # Track removal
        track_remove_from_cart(request, cart_item.product)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    elif quantity > cart_item.product.stock:
        messages.error(request, f'Only {cart_item.product.stock} items available in stock.')
    else:
        # Track update
        track_update_cart(request, cart_item.product, quantity)
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated.')
    
    return redirect('store:cart')


@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify the cart item belongs to the current user/session
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            messages.error(request, 'Invalid cart item.')
            return redirect('store:cart')
    else:
        if cart_item.cart.session_key != request.session.session_key:
            messages.error(request, 'Invalid cart item.')
            return redirect('store:cart')
    
    product_name = cart_item.product.name
    product = cart_item.product
    
    # Track removal
    track_remove_from_cart(request, product)
    
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart.')
    
    return redirect('store:cart')


@login_required
def checkout(request):
    """Checkout page"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')
    
    # Track checkout started
    track_checkout_started(request, cart_items_count=cart.items.count(), cart_total=cart.total_price)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address_line1=form.cleaned_data['address_line1'],
                address_line2=form.cleaned_data['address_line2'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
                total_amount=cart.total_price,
                payment_status='completed',  # Assume payment is completed
                notes=form.cleaned_data.get('notes', '')
            )
            
            # Create order items and update product stock
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity
                )
                # Update product stock and units sold
                product = cart_item.product
                product.stock -= cart_item.quantity
                product.units_sold += cart_item.quantity
                product.save()
            
            # Track order placed
            track_order_placed(request, order)
            
            # Clear cart
            cart.items.all().delete()
            
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('store:order_detail', order_number=order.order_number)
    else:
        # Pre-fill form with user data
        initial_data = {
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail view"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'store/order_detail.html', context)


@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'store/order_history.html', context)


def autocomplete_search(request):
    """
    API endpoint for search autocomplete suggestions.
    Returns JSON array of suggested search terms.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        # Return trending searches for empty/short queries
        suggestions = get_trending_searches(user=request.user, limit=8)
    else:
        # Get autocomplete suggestions based on partial query
        suggestions = get_autocomplete_suggestions(query, user=request.user, limit=8)
    
    return JsonResponse({
        'suggestions': suggestions,
        'query': query
    })


def trending_searches(request):
    """
    API endpoint for trending searches.
    Returns JSON array of trending search terms based on user interactions.
    """
    limit = int(request.GET.get('limit', 10))
    trending = get_trending_searches(user=request.user, limit=limit)
    
    return JsonResponse({
        'trending': trending,
        'count': len(trending)
    })
