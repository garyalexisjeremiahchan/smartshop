import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartshop.settings')
django.setup()

from django.contrib.auth.models import User
from store.recommendations import get_ai_recommended_products
import traceback

try:
    # Test with a specific user
    user = User.objects.filter(is_superuser=False).first()
    if user:
        print(f"Testing AI recommendations for user: {user.username}")
        results = get_ai_recommended_products(user=user, limit=8)
    else:
        print("Testing AI recommendations for anonymous user")
        results = get_ai_recommended_products(user=None, limit=8)
    
    print(f'\nGot {len(results)} recommendations:')
    print('-' * 60)
    for p, score in results:
        print(f'{p.name}: {score}%')
    print('-' * 60)
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
