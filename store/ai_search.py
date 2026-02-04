"""
AI-powered search utilities for SmartShop using OpenAI API.
Provides natural language search capabilities with context understanding, 
synonyms recognition, and user preference awareness.
"""
import json
from openai import OpenAI
from django.conf import settings
from django.db.models import Q
from .models import Product, UserInteraction


def get_ai_search_results(query, user=None, limit=20):
    """
    Perform AI-powered product search using natural language query.
    
    Args:
        query: Natural language search query from user
        user: Django User object for personalized results (None for anonymous)
        limit: Maximum number of products to return
        
    Returns:
        List of tuples: [(product, relevance_score, reason), ...]
    """
    try:
        # Get API key from Django settings
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in settings")
        
        # Get user context for personalization
        user_context = ""
        if user and user.is_authenticated:
            # Get user's recent interactions to understand preferences
            recent_interactions = UserInteraction.objects.filter(
                user=user,
                interaction_type__in=['view_product', 'add_to_cart', 'order_placed']
            ).select_related('product', 'category').order_by('-timestamp')[:20]
            
            if recent_interactions:
                user_prefs = {}
                for interaction in recent_interactions:
                    if interaction.product:
                        category = interaction.product.category.name
                        user_prefs[category] = user_prefs.get(category, 0) + 1
                
                top_categories = sorted(user_prefs.items(), key=lambda x: x[1], reverse=True)[:3]
                user_context = f"User has shown interest in: {', '.join([cat for cat, _ in top_categories])}"
        
        # Get all available products with their details
        all_products = Product.objects.filter(is_active=True).select_related('category')
        
        # Create product catalog for AI
        product_catalog = []
        for product in all_products:
            product_info = {
                'id': product.id,
                'name': product.name,
                'category': product.category.name,
                'description': product.description[:200],  # Truncate for token efficiency
                'price': float(product.price),
                'in_stock': product.is_in_stock,
                'rating': product.average_rating,
                'popularity': product.units_sold
            }
            product_catalog.append(product_info)
        
        # Create AI prompt
        prompt = f"""You are an intelligent e-commerce search assistant. Analyze the following search query and return the most relevant products from the catalog.

Search Query: "{query}"

{user_context}

Product Catalog (Total: {len(product_catalog)} products):
{json.dumps(product_catalog, indent=2)}

Instructions:
1. Understand the search intent - what is the user really looking for?
2. Consider synonyms and related terms (e.g., "laptop" = "notebook computer", "phone" = "smartphone", "TV" = "television")
3. Consider user preferences if provided
4. Match products based on:
   - Product name relevance
   - Category relevance
   - Description keywords
   - Price range if mentioned (e.g., "cheap", "budget", "expensive", "premium")
   - Quality indicators (rating, popularity)
5. Return products in order of relevance

Return ONLY a JSON array with this exact format (maximum {limit} products):
[
  {{
    "product_id": 123,
    "relevance_score": 95.5,
    "reason": "Brief explanation of why this matches (20 words max)"
  }},
  ...
]

The relevance_score should be 0-100 representing how well the product matches the search intent.
Only include products with relevance_score > 30.
"""
        
        # Call OpenAI API
        client = OpenAI(api_key=api_key)
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert e-commerce search engine that understands natural language and user intent. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent results
            max_tokens=2000
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown formatting)
        if '```json' in ai_response:
            ai_response = ai_response.split('```json')[1].split('```')[0].strip()
        elif '```' in ai_response:
            ai_response = ai_response.split('```')[1].split('```')[0].strip()
        
        recommendations = json.loads(ai_response)
        
        # Map recommendations to actual products
        search_results = []
        for rec in recommendations[:limit]:
            try:
                product = Product.objects.get(
                    id=rec['product_id'],
                    is_active=True
                )
                relevance_score = float(rec.get('relevance_score', 50.0))
                reason = rec.get('reason', 'Matches your search')
                search_results.append((product, relevance_score, reason))
            except Product.DoesNotExist:
                continue
        
        return search_results
        
    except Exception as e:
        # Fallback to traditional search if AI fails
        print(f"AI search error: {e}")
        return fallback_search(query, limit)


def fallback_search(query, limit=20):
    """
    Traditional keyword-based search as fallback.
    
    Args:
        query: Search query string
        limit: Maximum number of products to return
        
    Returns:
        List of tuples: [(product, relevance_score, reason), ...]
    """
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    ).select_related('category').order_by('-units_sold')[:limit]
    
    # Assign basic relevance scores
    results = []
    for product in products:
        # Higher score if query matches name exactly
        if query.lower() in product.name.lower():
            score = 90.0
        elif query.lower() in product.category.name.lower():
            score = 70.0
        else:
            score = 60.0
        
        results.append((product, score, "Keyword match"))
    
    return results


def get_trending_searches(user=None, limit=10):
    """
    Get trending search queries based on recent user interactions.
    Used for autocomplete suggestions.
    
    Args:
        user: Django User object for personalized suggestions (None for anonymous)
        limit: Number of suggestions to return
        
    Returns:
        List of trending search terms/product names
    """
    try:
        # Get recent search interactions
        search_interactions = UserInteraction.objects.filter(
            interaction_type='search'
        ).order_by('-timestamp')[:100]
        
        # Count search query frequencies
        search_counts = {}
        for interaction in search_interactions:
            query = interaction.search_query
            if query:
                query = query.lower().strip()
                if len(query) >= 2:  # Minimum 2 characters
                    search_counts[query] = search_counts.get(query, 0) + 1
        
        # Get trending product names from popular products
        trending_products = Product.objects.filter(
            is_active=True
        ).order_by('-units_sold')[:limit * 2]
        
        trending_terms = []
        
        # Add top searched terms
        top_searches = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)[:limit // 2]
        trending_terms.extend([term for term, _ in top_searches])
        
        # Add popular product names
        for product in trending_products:
            if len(trending_terms) >= limit:
                break
            # Add product name if not already in list
            product_name = product.name.lower()
            if product_name not in trending_terms and product.name not in trending_terms:
                trending_terms.append(product.name)
        
        # Add popular category names
        if len(trending_terms) < limit:
            from .models import Category
            categories = Category.objects.filter(is_active=True)[:limit]
            for category in categories:
                if len(trending_terms) >= limit:
                    break
                if category.name.lower() not in [t.lower() for t in trending_terms]:
                    trending_terms.append(category.name)
        
        return trending_terms[:limit]
        
    except Exception as e:
        print(f"Error getting trending searches: {e}")
        # Fallback to popular product names
        products = Product.objects.filter(is_active=True).order_by('-units_sold')[:limit]
        return [p.name for p in products]


def get_autocomplete_suggestions(partial_query, user=None, limit=8):
    """
    Get autocomplete suggestions for a partial search query.
    
    Args:
        partial_query: Partial search string (e.g., "lap" for "laptop")
        user: Django User object for personalized suggestions
        limit: Number of suggestions to return
        
    Returns:
        List of suggested search terms
    """
    if not partial_query or len(partial_query) < 2:
        # Return trending searches if query too short
        return get_trending_searches(user, limit)
    
    suggestions = []
    query_lower = partial_query.lower()
    
    # Get product name matches
    products = Product.objects.filter(
        name__icontains=partial_query,
        is_active=True
    ).order_by('-units_sold')[:limit]
    
    for product in products:
        if product.name not in suggestions:
            suggestions.append(product.name)
    
    # Get category matches
    if len(suggestions) < limit:
        from .models import Category
        categories = Category.objects.filter(
            name__icontains=partial_query,
            is_active=True
        )[:limit - len(suggestions)]
        
        for category in categories:
            if category.name not in suggestions:
                suggestions.append(category.name)
    
    # Fill with trending searches if needed
    if len(suggestions) < limit:
        trending = get_trending_searches(user, limit)
        for term in trending:
            if len(suggestions) >= limit:
                break
            if query_lower in term.lower() and term not in suggestions:
                suggestions.append(term)
    
    return suggestions[:limit]
