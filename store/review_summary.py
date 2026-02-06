"""
Utility functions for generating AI-powered review summaries using OpenAI
"""
from openai import OpenAI
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json


def generate_review_summary(product):
    """
    Generate AI-powered summary of product reviews using OpenAI.
    
    Args:
        product: Product instance
        
    Returns:
        dict: Contains summary, pros, cons, and sentiment
    """
    from .models import Review
    
    # Get approved reviews for this product
    reviews = Review.objects.filter(
        product=product, 
        is_approved=True
    ).order_by('-created_at')
    
    review_count = reviews.count()
    
    # Need at least 3 reviews to generate summary
    if review_count < 3:
        return None
    
    # Check if we need to regenerate the summary
    # Only regenerate if:
    # 1. No summary exists, or
    # 2. Summary is older than 1 day AND there are new reviews
    if product.review_summary_generated_at:
        time_since_generation = timezone.now() - product.review_summary_generated_at
        if time_since_generation < timedelta(days=1):
            # Summary is fresh, don't regenerate
            return None
        if product.review_summary_review_count == review_count:
            # No new reviews, don't regenerate
            return None
    
    # Prepare review data for OpenAI
    review_texts = []
    for review in reviews:
        review_texts.append({
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment
        })
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Create the prompt
        prompt = f"""Analyze the following customer reviews for "{product.name}" and provide a structured summary.

Reviews ({review_count} total):
{json.dumps(review_texts, indent=2)}

Please provide:
1. A concise overall summary (2-3 sentences) highlighting the key points
2. Top 3-5 PROS mentioned by customers (as bullet points)
3. Top 3-5 CONS mentioned by customers (as bullet points)
4. Overall sentiment (choose one: positive, neutral, or negative)

Format your response as JSON with the following structure:
{{
    "summary": "overall summary text",
    "pros": ["pro 1", "pro 2", "pro 3"],
    "cons": ["con 1", "con 2", "con 3"],
    "sentiment": "positive|neutral|negative"
}}

Be objective and focus on the most frequently mentioned points. If there are very few or no cons, you can list fewer items or note that customers are generally satisfied."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes product reviews and provides objective summaries to help shoppers make informed decisions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Update product with the summary
        product.review_summary = result.get('summary', '')
        product.review_summary_pros = '\n'.join(result.get('pros', []))
        product.review_summary_cons = '\n'.join(result.get('cons', []))
        product.review_summary_sentiment = result.get('sentiment', 'neutral')
        product.review_summary_generated_at = timezone.now()
        product.review_summary_review_count = review_count
        product.save(update_fields=[
            'review_summary',
            'review_summary_pros',
            'review_summary_cons',
            'review_summary_sentiment',
            'review_summary_generated_at',
            'review_summary_review_count'
        ])
        
        return result
        
    except Exception as e:
        print(f"Error generating review summary: {str(e)}")
        return None


def should_regenerate_summary(product):
    """
    Check if product review summary should be regenerated.
    
    Args:
        product: Product instance
        
    Returns:
        bool: True if summary should be regenerated
    """
    from .models import Review
    
    review_count = Review.objects.filter(
        product=product,
        is_approved=True
    ).count()
    
    # Need at least 3 reviews
    if review_count < 3:
        return False
    
    # No summary exists yet
    if not product.review_summary_generated_at:
        return True
    
    # Check if summary is older than 1 day
    time_since_generation = timezone.now() - product.review_summary_generated_at
    if time_since_generation < timedelta(days=1):
        return False
    
    # Check if there are new reviews
    if product.review_summary_review_count < review_count:
        return True
    
    return False
