import os
import json
from openai import OpenAI
from django.conf import settings
from .models import UserInteraction, Product


def get_ai_recommended_products(user=None, limit=8):
    """
    Generate product recommendations using OpenAI API based on user interactions.
    Returns list of tuples: (product, relevance_score)
    
    Args:
        user: Django User object for personalized recommendations (None for anonymous)
        limit: Number of products to recommend
    """
    try:
        # Get API key from Django settings
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in settings")
        
        # Get recent user interactions (user-specific if logged in)
        interaction_filter = {
            'interaction_type__in': ['view_product', 'add_to_cart', 'order_placed']
        }
        
        if user and user.is_authenticated:
            # Get user's own interactions (last 50) + global trends (last 50)
            user_interactions = UserInteraction.objects.select_related(
                'product', 'category'
            ).filter(
                user=user,
                **interaction_filter
            ).order_by('-timestamp')[:50]
            
            global_interactions = UserInteraction.objects.select_related(
                'product', 'category'
            ).filter(
                **interaction_filter
            ).exclude(
                user=user
            ).order_by('-timestamp')[:50]
            
            # Combine with higher weight on user's interactions
            recent_interactions = list(user_interactions) + list(global_interactions)
        else:
            # Anonymous user - use global trends
            recent_interactions = list(UserInteraction.objects.select_related(
                'product', 'category'
            ).filter(
                **interaction_filter
            ).order_by('-timestamp')[:100])
        
        if not recent_interactions:
            # Return popular products if no interactions
            products = Product.objects.filter(is_active=True).order_by('-units_sold')[:limit]
            return [(product, 85.0) for product in products]
        
        # Prepare interaction data for AI
        interaction_summary = {}
        for interaction in recent_interactions:
            if interaction.product:
                product_name = interaction.product.name
                category_name = interaction.product.category.name
                key = f"{product_name} ({category_name})"
                
                if key not in interaction_summary:
                    interaction_summary[key] = {
                        'views': 0,
                        'cart_adds': 0,
                        'purchases': 0,
                        'product_id': interaction.product.id
                    }
                
                if interaction.interaction_type == 'view_product':
                    interaction_summary[key]['views'] += 1
                elif interaction.interaction_type == 'add_to_cart':
                    interaction_summary[key]['cart_adds'] += 1
                elif interaction.interaction_type == 'order_placed':
                    interaction_summary[key]['purchases'] += 1
        
        # Get all available products
        all_products = Product.objects.filter(is_active=True).values_list('id', 'name', 'category__name')
        product_catalog = [f"{name} ({cat})" for _, name, cat in all_products]
        
        # Create prompt for OpenAI
        user_context = "a specific user" if user and user.is_authenticated else "anonymous visitors"
        prompt = f"""Based on the following user interaction data from an e-commerce website, recommend the top {limit} products that would be most relevant for {user_context}.

User Interaction Data (last 100 interactions, with emphasis on this user's activity):
{json.dumps(interaction_summary, indent=2)}

Available Products in Catalog:
{json.dumps(product_catalog[:50], indent=2)}  

Please analyze the interaction patterns (views, cart additions, purchases) and recommend {limit} products that:
1. Have high engagement (views, cart adds, purchases)
2. Represent diverse categories for variety
3. Show trending patterns
4. Balance popularity with discovery

Return ONLY a JSON array with this exact format:
[
  {{"product": "Product Name (Category Name)", "relevance_score": 95.5, "reason": "brief reason"}},
  ...
]

The relevance_score should be between 0-100 representing how strongly you recommend this product.
"""
        
        # Call OpenAI API
        client = OpenAI(api_key=api_key)
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert e-commerce product recommendation engine. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case there's markdown formatting)
        if '```json' in ai_response:
            ai_response = ai_response.split('```json')[1].split('```')[0].strip()
        elif '```' in ai_response:
            ai_response = ai_response.split('```')[1].split('```')[0].strip()
        
        recommendations = json.loads(ai_response)
        
        # Map recommendations to actual products
        recommended_products = []
        for rec in recommendations[:limit]:
            product_name = rec['product'].split(' (')[0]  # Extract product name
            try:
                product = Product.objects.filter(
                    name__icontains=product_name,
                    is_active=True
                ).first()
                
                if product:
                    relevance_score = float(rec.get('relevance_score', 80.0))
                    recommended_products.append((product, relevance_score))
            except Product.DoesNotExist:
                continue
        
        # Fill with popular products if we don't have enough
        if len(recommended_products) < limit:
            existing_ids = [p[0].id for p in recommended_products]
            additional = Product.objects.filter(
                is_active=True
            ).exclude(
                id__in=existing_ids
            ).order_by('-units_sold')[: limit - len(recommended_products)]
            
            for product in additional:
                recommended_products.append((product, 75.0))
        
        return recommended_products[:limit]
        
    except Exception as e:
        # Fallback to popular products if AI fails
        print(f"AI recommendation error: {e}")
        products = Product.objects.filter(is_active=True).order_by('-units_sold')[:limit]
        return [(product, 80.0) for product in products]
