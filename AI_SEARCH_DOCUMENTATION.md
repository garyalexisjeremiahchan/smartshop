# AI-Powered Search Feature Documentation

## Overview
SmartShop now features an advanced AI-powered search system that uses OpenAI's GPT models to understand natural language queries, recognize synonyms, and provide contextually relevant product results based on user preferences and behavior.

## Features

### 1. Natural Language Understanding
- **Context-Aware Search**: Understands the intent behind search queries
- **Synonym Recognition**: Recognizes related terms (e.g., "laptop" = "notebook computer", "TV" = "television")
- **Smart Interpretation**: Handles colloquial language and informal queries

### 2. Personalized Search Results
- **User Preference Integration**: Considers user's browsing and purchase history
- **Behavioral Analysis**: Analyzes past interactions (views, cart additions, purchases)
- **Category Preferences**: Prioritizes products from categories the user has shown interest in

### 3. Intelligent Ranking
- **Relevance Scoring**: Each result has a relevance score (0-100)
- **Multi-Factor Ranking**: Considers:
  - Product name relevance
  - Category relevance
  - Description keyword matching
  - Price range mentions (e.g., "cheap", "budget", "premium")
  - Product ratings and popularity
  - User preferences

### 4. Advanced Frontend Features

#### Autocomplete Suggestions
- **Dynamic Suggestions**: Real-time suggestions as user types
- **Trending Searches**: Shows popular searches when input is empty
- **Smart Filtering**: Suggests products, categories, and popular search terms

#### Debounce Implementation
- **Optimized Performance**: 300ms debounce delay prevents excessive API calls
- **Smooth UX**: Reduces server load while maintaining responsiveness
- **Loading Indicators**: Visual feedback during search

#### Keyboard Navigation
- **Arrow Keys**: Navigate through suggestions with up/down arrows
- **Enter**: Select highlighted suggestion
- **Escape**: Close autocomplete dropdown

## Technical Implementation

### Backend Components

#### 1. AI Search Engine (`store/ai_search.py`)

```python
# Main search function
get_ai_search_results(query, user=None, limit=20)
```
- Analyzes user query with OpenAI GPT
- Considers user interaction history
- Returns ranked product list with relevance scores

```python
# Autocomplete function
get_autocomplete_suggestions(partial_query, user=None, limit=8)
```
- Provides real-time search suggestions
- Matches product names, categories
- Falls back to trending searches

```python
# Trending searches
get_trending_searches(user=None, limit=10)
```
- Analyzes recent search interactions
- Returns popular search terms and products
- Used for autocomplete when input is empty

#### 2. View Updates (`store/views.py`)

**AI Search Integration**:
```python
def category_list(request, slug=None):
    # AI-powered search with caching
    if search_query:
        ai_results = get_ai_search_results(search_query, user=request.user, limit=50)
        # Cache for 30 minutes
```

**API Endpoints**:
- `/api/autocomplete/`: Returns autocomplete suggestions
- `/api/trending/`: Returns trending searches

### Frontend Components

#### 1. Search Bar (`templates/base.html`)
- Enhanced input with autocomplete dropdown
- Visual indicators for AI-powered search
- Accessible ARIA labels

#### 2. Autocomplete Styles (`static/css/style.css`)
```css
.autocomplete-dropdown
.autocomplete-header
#autocompleteList li
.search-loading
```

#### 3. JavaScript Implementation (`static/js/main.js`)
- **Debounce Function**: Delays API calls until user stops typing
- **Fetch Autocomplete**: Async API calls for suggestions
- **Keyboard Navigation**: Arrow keys, Enter, Escape support
- **Click Handlers**: Mouse interaction with suggestions
- **Highlight Matching**: Bolds matching text in suggestions

## How It Works

### Search Flow

1. **User Types Query**
   - Debounce timer starts (300ms)
   - Loading indicator shows

2. **Autocomplete Triggered**
   - After debounce delay, fetch suggestions from `/api/autocomplete/`
   - Display dropdown with matching products/categories/trending

3. **User Submits Search**
   - Query sent to category_list view
   - AI search engine processes query:
     - Fetches user interaction history
     - Builds product catalog
     - Creates OpenAI prompt with context
     - Receives AI-ranked results
   - Results cached for 30 minutes
   - Products displayed in relevance order

4. **Result Display**
   - Products shown in AI-determined order
   - Relevance scores used internally
   - Standard product cards displayed

### Caching Strategy

**Search Results Cache**:
- Key: `ai_search_{user_id}_{query}`
- Duration: 30 minutes (1800 seconds)
- Per-user caching for personalized results

**Recommendation Cache**:
- Key: `ai_recommended_products_{user_id}`
- Duration: 1 hour (3600 seconds)

### Fallback Mechanisms

If AI search fails, system falls back to:
1. Traditional keyword-based search
2. Basic relevance scoring
3. Popularity-based sorting

## API Reference

### Autocomplete API

**Endpoint**: `/api/autocomplete/`

**Method**: GET

**Parameters**:
- `q`: Search query (min 2 characters)

**Response**:
```json
{
  "suggestions": ["Laptop", "Smartphone", "Headphones"],
  "query": "lap"
}
```

### Trending Searches API

**Endpoint**: `/api/trending/`

**Method**: GET

**Parameters**:
- `limit`: Number of results (default: 10)

**Response**:
```json
{
  "trending": ["iPhone", "Samsung TV", "Gaming Laptop"],
  "count": 3
}
```

## Configuration

### Required Settings (`settings.py`)

```python
# OpenAI Configuration
OPENAI_API_KEY = 'your-api-key-here'
OPENAI_MODEL = 'gpt-4o-mini'  # or 'gpt-4'

# Caching (already configured)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...
```

## Usage Examples

### Natural Language Queries

1. **Simple Product Search**
   - Query: "laptop"
   - Result: All laptop products ranked by relevance

2. **Descriptive Search**
   - Query: "cheap wireless headphones"
   - Result: Affordable headphones, prioritizing wireless models

3. **Category-Based**
   - Query: "gaming accessories"
   - Result: Gaming keyboards, mice, headsets, etc.

4. **Intent-Based**
   - Query: "something for video calls"
   - Result: Webcams, microphones, headsets

5. **Quality Indicators**
   - Query: "best premium smartphone"
   - Result: High-end phones with good ratings

## Performance Considerations

### Optimization Techniques

1. **Debouncing**: Reduces API calls by 80-90%
2. **Caching**: 30-minute cache for search results
3. **Token Efficiency**: Product descriptions truncated to 200 chars
4. **Async Loading**: Non-blocking autocomplete requests

### API Cost Management

- **Model**: Uses `gpt-4o-mini` by default (cost-effective)
- **Token Limits**: max_tokens=2000 for search
- **Caching**: Reduces repeated API calls
- **Fallback**: Free keyword search if API fails

## Testing

### Manual Testing

1. **Basic Search**: Type "laptop" and verify results
2. **Autocomplete**: Type "lap" and check suggestions
3. **Keyboard Nav**: Use arrow keys to navigate
4. **Trending**: Click empty search bar for trending
5. **Natural Language**: Try "cheap headphones under $50"

### Monitoring

Check logs for:
- `AI search error:` - API failures
- `AI recommendation error:` - Recommendation failures
- Cache hit rates

## Troubleshooting

### Common Issues

**No Autocomplete Appearing**
- Check JavaScript console for errors
- Verify `/api/autocomplete/` endpoint is accessible
- Ensure jQuery/Bootstrap is loaded

**AI Search Not Working**
- Verify OPENAI_API_KEY in settings
- Check API quota/billing
- Review error logs
- Falls back to keyword search automatically

**Slow Performance**
- Increase debounce delay (300ms → 500ms)
- Reduce search result limit
- Check cache configuration

## Future Enhancements

1. **Voice Search**: Add speech-to-text capability
2. **Image Search**: Search by product images
3. **Filters Integration**: AI-powered filter suggestions
4. **Search Analytics**: Track popular queries
5. **Multi-Language**: Support for multiple languages
6. **Spell Correction**: Auto-correct typos

## Security Considerations

- API keys stored in environment variables
- Rate limiting on autocomplete endpoints
- Input sanitization for search queries
- CSRF protection on forms

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Dependencies

- `openai>=2.16.0`: OpenAI Python client
- `django>=4.0`: Web framework
- Bootstrap 5.3.0: UI framework
- Bootstrap Icons: Icon library

## Credits

- OpenAI GPT-4o-mini: AI search engine
- Bootstrap 5: UI framework
- Django: Backend framework
