# AI Search Setup Guide

## Quick Start

### 1. Verify OpenAI Package
The `openai` package is already in requirements.txt. If you haven't installed it:

```bash
pip install openai
```

### 2. Configure OpenAI API Key

Add your OpenAI API key to `smartshop/settings.py`:

```python
# AI Configuration
OPENAI_API_KEY = 'sk-your-api-key-here'  # Replace with your actual key
OPENAI_MODEL = 'gpt-4o-mini'  # Cost-effective option (recommended)
# OPENAI_MODEL = 'gpt-4'  # More powerful but expensive
```

**Or use environment variables (recommended for production):**

1. Create/update `.env` file in project root:
```
OPENAI_API_KEY=sk-your-api-key-here
```

2. Update settings.py to read from environment:
```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
```

3. Install python-dotenv if needed:
```bash
pip install python-dotenv
```

### 3. Test the Installation

Run the Django development server:

```bash
python manage.py runserver
```

### 4. Test AI Search

1. **Open your browser** to http://localhost:8000
2. **Click on the search bar** - You should see trending searches
3. **Type "lap"** - You should see autocomplete suggestions
4. **Search for "cheap laptop"** - Should return AI-ranked results

### 5. Verify Features

✅ **Autocomplete**: Type in search bar, see suggestions dropdown  
✅ **Debounce**: Notice smooth typing without lag  
✅ **Keyboard Navigation**: Use arrow keys to navigate suggestions  
✅ **Trending**: Empty search shows trending items  
✅ **AI Results**: Search results are contextually relevant  

## Testing Commands

### Test Autocomplete API
```bash
# Open in browser or use curl
curl "http://localhost:8000/api/autocomplete/?q=lap"
```

Expected response:
```json
{
  "suggestions": ["Laptop", "Gaming Laptop", "Laptop Stand"],
  "query": "lap"
}
```

### Test Trending API
```bash
curl "http://localhost:8000/api/trending/?limit=5"
```

Expected response:
```json
{
  "trending": ["iPhone", "Laptop", "Headphones", "TV", "Camera"],
  "count": 5
}
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not found in settings"

**Solution**: Add the API key to settings.py as shown above

### Issue: No autocomplete showing

**Solution**: 
1. Check browser console for JavaScript errors (F12)
2. Verify `/api/autocomplete/` endpoint works
3. Clear browser cache

### Issue: Search returns no results

**Solution**:
1. Ensure products exist in database
2. Check if products are active (is_active=True)
3. Verify OpenAI API key is valid
4. System will fallback to keyword search if AI fails

### Issue: Slow search performance

**Solution**:
1. Check your internet connection (API calls to OpenAI)
2. Increase cache duration in views.py
3. Reduce the number of products sent to AI (limit parameter)

## Development Tips

### Customize Debounce Delay

Edit `static/js/main.js` line ~115:
```javascript
}, 300)); // Change 300 to desired milliseconds
```

### Adjust Cache Duration

Edit `store/views.py` around line 68:
```python
cache.set(cache_key, ai_results, 1800)  # Change 1800 (30 min) to desired seconds
```

### Change AI Model

In settings.py:
```python
OPENAI_MODEL = 'gpt-4'  # More powerful, more expensive
# or
OPENAI_MODEL = 'gpt-4o-mini'  # Faster, cheaper (default)
```

### Customize Result Limit

Edit `store/views.py` around line 65:
```python
ai_results = get_ai_search_results(search_query, user=request.user, limit=50)
# Change limit=50 to desired number
```

## Production Deployment

### 1. Use Environment Variables
Never commit API keys to git. Use environment variables.

### 2. Enable Redis Caching
For better performance in production, use Redis:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Monitor API Usage
- Track OpenAI API costs in dashboard
- Set up usage alerts
- Consider implementing rate limiting

### 4. Static Files
Collect static files for production:
```bash
python manage.py collectstatic
```

## Cost Estimation

Using `gpt-4o-mini`:
- ~1,000 searches/day = ~$0.50/day
- Caching reduces actual API calls by ~70%

Using `gpt-4`:
- ~1,000 searches/day = ~$5-10/day
- Recommend using only for high-value applications

## Next Steps

1. ✅ Test all features
2. ✅ Customize debounce/cache settings
3. ✅ Add sample products if database is empty
4. ✅ Monitor API usage
5. ✅ Consider adding analytics

## Support

For issues or questions:
- Check AI_SEARCH_DOCUMENTATION.md for detailed info
- Review Django logs for errors
- Check OpenAI API status
