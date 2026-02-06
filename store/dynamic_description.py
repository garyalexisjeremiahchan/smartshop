"""
Dynamic Product Description Generator using OpenAI API

This module generates engaging, sales-focused product descriptions based on:
- Existing product descriptions
- Product specifications
- Customer reviews
- Product images (metadata)
"""

from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class DynamicDescriptionGenerator:
    """Generate dynamic product descriptions using OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        
    def needs_regeneration(self, product):
        """
        Check if product description needs regeneration
        
        Returns True if:
        - No dynamic description exists
        - Description is older than 1 week
        - Product has been updated since description was generated
        """
        if not product.dynamic_description or not product.dynamic_description_generated_at:
            return True
        
        # Check if description is older than 1 week
        one_week_ago = timezone.now() - timedelta(days=7)
        if product.dynamic_description_generated_at < one_week_ago:
            return True
        
        # Check if product was updated after description was generated
        if product.updated_at > product.dynamic_description_generated_at:
            return True
        
        return False
    
    def _build_prompt(self, product):
        """Build the prompt for OpenAI API"""
        
        # Get recent reviews (limit to 10 most recent)
        recent_reviews = product.reviews.filter(is_approved=True).order_by('-created_at')[:10]
        
        # Build review summary
        review_text = ""
        if recent_reviews.exists():
            review_summaries = []
            for review in recent_reviews:
                review_summaries.append(f"- {review.rating}/5 stars: {review.comment[:100]}")
            review_text = "\n".join(review_summaries)
        else:
            review_text = "No reviews yet"
        
        # Build the prompt
        prompt = f"""You are a professional copywriter creating engaging product descriptions for an e-commerce website.

Product Name: {product.name}
Category: {product.category.name}
Price: ${product.price}
Units Sold: {product.units_sold}

Current Description:
{product.description}

Specifications:
{product.specifications if product.specifications else 'Not available'}

Customer Reviews (Recent):
{review_text}

Task: Transform the above information into an engaging, persuasive product description that:
1. Highlights key features and benefits (not just specifications)
2. Uses emotional language to create desire
3. Addresses customer needs based on reviews (if available)
4. Keeps the tone professional yet conversational
5. Focuses on how the product improves the customer's life
6. Is 3-4 sentences long (around 60-100 words)
7. Ends with a subtle call-to-action or benefit statement

Example transformation:
Before: "Blender with 450-watt motor, 3 speed settings and pulse function, Stainless steel blades, Dishwasher safe parts"
After: "Unleash your culinary creativity with our 450-watt blender, improving your everyday blending and delivering a smooth consistency with minimal effort. With 3 speed settings and pulse function, you can handle any recipe and ensure smooth blending with no lumps in as little as 30 seconds. The stainless steel blade ensures precision cutting, and dishwasher safe parts makes cleaning up a breeze, giving you more time to savor your culinary creations."

Write ONLY the new product description, nothing else."""

        return prompt
    
    def generate_description(self, product):
        """
        Generate dynamic product description using OpenAI API
        
        Args:
            product: Product instance
            
        Returns:
            str: Generated description or None if failed
        """
        if not self.client:
            logger.error("OpenAI API key not configured")
            return None
        
        try:
            prompt = self._build_prompt(product)
            
            # Call OpenAI API (new version)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional e-commerce copywriter who creates compelling product descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.7,
            )
            
            # Extract the generated description
            description = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            if description.startswith('"') and description.endswith('"'):
                description = description[1:-1]
            
            logger.info(f"Generated dynamic description for product: {product.name}")
            return description
            
        except Exception as e:
            logger.error(f"Error generating dynamic description for {product.name}: {str(e)}")
            return None
    
    def update_product_description(self, product, force=False):
        """
        Update product with dynamic description if needed
        
        Args:
            product: Product instance
            force: If True, regenerate even if not needed
            
        Returns:
            bool: True if description was updated, False otherwise
        """
        if not force and not self.needs_regeneration(product):
            logger.debug(f"Dynamic description for {product.name} is still fresh")
            return False
        
        description = self.generate_description(product)
        
        if description:
            product.dynamic_description = description
            product.dynamic_description_generated_at = timezone.now()
            product.save(update_fields=['dynamic_description', 'dynamic_description_generated_at'])
            return True
        
        return False
