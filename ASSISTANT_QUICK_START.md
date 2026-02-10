# Virtual Shopping Assistant - Quick Start

## ⚡ Quick Setup (5 Minutes)

### Step 1: Add OpenAI API Key

Edit your `.env` file and add:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Don't have an API key?** Get one at: https://platform.openai.com/api-keys

### Step 2: Run Migrations

```bash
python manage.py makemigrations assistant
python manage.py migrate
```

### Step 3: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 4: Start Server

```bash
python manage.py runserver
```

### Step 5: Test It!

1. Open http://127.0.0.1:8000/
2. Look for purple floating button (bottom-right corner)
3. Click it to open the chat
4. Try: "Show me popular products"

## ✅ What Was Installed

### New Files Created

**Backend:**
- `assistant/` - Complete Django app with:
  - `models.py` - Conversation tracking
  - `views.py` - Chat endpoint
  - `services.py` - OpenAI orchestration
  - `tools.py` - Database query tools
  - `prompts.py` - System prompt and tool schemas
  - `urls.py` - API routes
  - `admin.py` - Admin interface

**Frontend:**
- `templates/assistant/widget.html` - Chat UI
- `static/assistant/assistant.css` - Styles
- `static/assistant/assistant.js` - Frontend logic

### Modified Files

- `smartshop/settings.py` - Added 'assistant' to INSTALLED_APPS
- `smartshop/urls.py` - Added `/assistant/` routes
- `templates/base.html` - Included widget on all pages
- `templates/store/product_detail.html` - Added page context

## 🧪 Quick Test Commands

### Test 1: Basic Search
```
"Show me laptops under $1000"
```
**Expected:** Product cards with laptops, prices shown

### Test 2: Product Details
*Navigate to any product page first*
```
"Tell me about this product"
```
**Expected:** Recognizes current product, shows details

### Test 3: Recommendations
```
"Recommend me a phone with good camera"
```
**Expected:** 3-5 phone suggestions with reasoning

### Test 4: Availability
*On a product page*
```
"Is this in stock?"
```
**Expected:** Current stock status

### Test 5: Reviews
```
"What do customers say about this?"
```
**Expected:** Review summary with pros/cons

## 🎯 Key Features

✅ **Tool-Based** - Never guesses data, always queries database
✅ **Context-Aware** - Knows what page user is viewing
✅ **Mobile Responsive** - Works on all devices
✅ **Conversation Memory** - Remembers chat history
✅ **Rate Limited** - Prevents abuse (20 requests/min)
✅ **Product Cards** - Rich product previews
✅ **Real-time** - Instant responses

## 📊 Available Tools

The assistant can:
1. **Search products** - By keyword, category, price, rating
2. **Get product details** - Full specs and descriptions
3. **Check availability** - Stock levels
4. **Summarize reviews** - Customer feedback
5. **Find similar products** - Alternatives
6. **Browse categories** - All product types
7. **Get specifications** - Technical details

## 🔧 Troubleshooting

### Widget not showing?
1. Check: `python manage.py collectstatic`
2. Hard refresh: Ctrl+F5
3. Check browser console for errors

### "OpenAI API Error"?
1. Verify `.env` has correct API key
2. Check API key has credits: https://platform.openai.com/usage
3. Check Django console for error details

### No products showing?
1. Ensure products exist: `http://127.0.0.1:8000/admin/store/product/`
2. Check products are `is_active=True`
3. Try: "What categories do you have?"

### Rate limited?
Wait 60 seconds or adjust limit in `assistant/views.py`:
```python
@rate_limit(max_requests=50, window_seconds=60)
```

## 📝 Configuration

### Change AI Model
In `.env`:
```env
OPENAI_MODEL=gpt-4o  # More powerful but costs more
```

### Customize Appearance
Edit `static/assistant/assistant.css`:
```css
.assistant-fab {
    background: linear-gradient(135deg, #YOUR_BRAND_COLOR);
}
```

### Adjust System Prompt
Edit `assistant/prompts.py` to change assistant personality

## 💰 Cost Estimation

**GPT-4o-mini** (recommended):
- ~$0.30-$0.50 per 1000 conversations
- Very affordable for testing

**GPT-4o** (premium):
- ~$3-$5 per 1000 conversations
- Higher quality responses

**Tip:** Start with gpt-4o-mini, upgrade if needed

## 🎉 You're All Set!

The Virtual Shopping Assistant is now live on your site!

For detailed documentation, see: `ASSISTANT_SETUP_GUIDE.md`

---

**Need Help?**
- Check Django console for errors
- Review browser console (F12)
- Check OpenAI dashboard for API issues
