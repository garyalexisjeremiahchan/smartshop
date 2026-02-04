# Autocomplete Troubleshooting Guide

## Issue: Autocomplete not showing when typing "lap"

### Diagnostic Steps

#### 1. Check Browser Console (F12)
Open your browser's developer console and look for:

**Expected Messages:**
```
AI Search autocomplete initialized successfully
Search input: lap
Fetching autocomplete for: lap
Received suggestions: [...]
```

**Error Messages to Look For:**
- `Search input element not found`
- `Autocomplete dropdown element not found`
- `Autocomplete list element not found`
- `Search form element not found`
- `Autocomplete error: [error details]`
- `AI Search autocomplete could not initialize - missing required elements`

#### 2. Check Network Tab (F12 → Network)
When you type "lap", you should see:
- **Request**: `GET /api/autocomplete/?q=lap`
- **Status**: `200 OK`
- **Response**: JSON with suggestions array

**If you don't see the request:**
- JavaScript is not running or event listener not attached
- Debounce is working but something else is wrong

**If you see 404 error:**
- URL routing issue - check `store/urls.py`

**If you see 500 error:**
- Backend error - check Django logs

#### 3. Verify HTML Elements Exist

**Open browser console and run:**
```javascript
console.log('searchInput:', document.getElementById('searchInput'));
console.log('autocompleteDropdown:', document.getElementById('autocompleteDropdown'));
console.log('autocompleteList:', document.getElementById('autocompleteList'));
console.log('searchForm:', document.getElementById('searchForm'));
```

**Expected result:** Each should show an HTML element, not `null`

**If any is null:**
- Template is not rendering correctly
- IDs don't match between base.html and main.js
- You're on a page that doesn't include base.html

#### 4. Test API Endpoint Directly

**In browser, navigate to:**
```
http://localhost:8000/api/autocomplete/?q=lap
```

**Expected Response:**
```json
{
  "suggestions": ["Laptop", "Gaming Laptop", "Laptop Stand", ...],
  "query": "lap"
}
```

**If you get an error:**
- Django server not running
- URL pattern not configured
- View function has an error
- No products in database

#### 5. Check if Django Server is Running

```bash
python manage.py runserver
```

Server should be running on `http://127.0.0.1:8000/`

#### 6. Verify Products Exist in Database

**In Django shell:**
```bash
python manage.py shell
```

```python
from store.models import Product
print(Product.objects.filter(name__icontains='lap').count())
# Should return > 0 if you have laptop products
```

#### 7. Check Static Files

**Verify the JavaScript file is being loaded:**
- Open browser → View Page Source
- Look for: `<script src="/static/js/main.js"></script>`
- Click on the link - file should load
- Check if file contains the autocomplete code (search for "fetchAutocomplete")

**If file doesn't load:**
```bash
python manage.py collectstatic
```

#### 8. Check Settings

**In `smartshop/settings.py`:**
```python
# Should have:
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# For production:
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### 9. Clear Browser Cache

- Press `Ctrl + Shift + Delete`
- Clear cached files
- Or use "Hard Reload": `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)

#### 10. Check for JavaScript Errors

**In console, look for:**
- Syntax errors
- Uncaught TypeError
- Promise rejection errors
- CORS errors (if API is on different domain)

---

## Common Issues & Solutions

### Issue 1: Elements Not Found
**Symptom:** Console shows "element not found" warnings

**Solution:**
1. Check `templates/base.html` has correct IDs:
   - `id="searchInput"`
   - `id="autocompleteDropdown"`
   - `id="autocompleteList"`
   - `id="searchForm"`

2. Verify you're on a page that extends `base.html`

### Issue 2: API Returns Empty Array
**Symptom:** Console shows `Received suggestions: []`

**Solutions:**
1. **No products in database** - Add products with names containing "lap"
2. **Products not active** - Ensure `is_active=True`
3. **Autocomplete function has bug** - Check `store/ai_search.py`

### Issue 3: Network Request Fails
**Symptom:** Console shows "Autocomplete error: Failed to fetch"

**Solutions:**
1. **Server not running** - Start Django: `python manage.py runserver`
2. **Wrong URL** - Check `/api/autocomplete/` exists in `store/urls.py`
3. **CORS issue** - If frontend on different domain, configure CORS

### Issue 4: Dropdown Doesn't Appear
**Symptom:** API works, suggestions received, but dropdown hidden

**Solutions:**
1. **CSS issue** - Check if `autocomplete-dropdown` class has `display: block` when active
2. **Z-index issue** - Dropdown behind other elements
3. **Position issue** - Dropdown not positioned correctly

**Debug CSS:**
```javascript
// In console when typing
const dropdown = document.getElementById('autocompleteDropdown');
console.log('Dropdown display:', dropdown.style.display);
console.log('Dropdown children:', dropdown.children.length);
```

### Issue 5: Debounce Too Long
**Symptom:** Autocomplete appears but very delayed

**Solution:** Reduce debounce delay in `static/js/main.js`:
```javascript
}, 300));  // Change to 150 for faster response
```

### Issue 6: JavaScript Not Running
**Symptom:** No console messages at all

**Solutions:**
1. **File not loaded** - Check browser DevTools → Sources → static/js/main.js
2. **Syntax error** - Check console for red error messages
3. **DOMContentLoaded not firing** - Script loaded after page ready
4. **Script blocked** - Check browser security settings

### Issue 7: OPENAI_API_KEY Not Configured
**Symptom:** Backend error when making search

**Solution:** Add to `smartshop/settings.py`:
```python
OPENAI_API_KEY = 'sk-your-api-key-here'
```

---

## Quick Fix Checklist

✅ **Django server running?**
```bash
python manage.py runserver
```

✅ **API endpoint works?**
```
http://localhost:8000/api/autocomplete/?q=lap
```

✅ **Browser console open? (F12)**

✅ **Hard refresh page? (Ctrl + Shift + R)**

✅ **Products exist in database?**

✅ **No JavaScript errors in console?**

✅ **Static files loaded correctly?**

✅ **Correct page (extends base.html)?**

---

## Step-by-Step Testing

### Test 1: Manual API Call
```bash
# In browser or curl:
http://localhost:8000/api/autocomplete/?q=lap
```
**Expected:** JSON response with suggestions

### Test 2: Check Elements
```javascript
// In browser console:
document.getElementById('searchInput')
```
**Expected:** `<input id="searchInput" ...>`

### Test 3: Trigger Manually
```javascript
// In browser console:
const event = new Event('input');
document.getElementById('searchInput').value = 'lap';
document.getElementById('searchInput').dispatchEvent(event);
```
**Expected:** Autocomplete dropdown appears after 300ms

### Test 4: Check Event Listener
```javascript
// In browser console:
getEventListeners(document.getElementById('searchInput'))
```
**Expected:** Shows `input` event listener

---

## If All Else Fails

1. **Clear all caches:**
   ```bash
   python manage.py collectstatic --clear
   ```

2. **Restart server:**
   ```bash
   # Stop server (Ctrl+C)
   python manage.py runserver
   ```

3. **Check updated JavaScript is loaded:**
   - View source → Check timestamp of main.js
   - Or add `?v=2` to script tag: `main.js?v=2`

4. **Try incognito/private window:**
   - Rules out cache/extension issues

5. **Check Django logs:**
   - Look for errors in terminal where server is running

6. **Verify file changes saved:**
   - Ensure `main.js` has the autocomplete code

---

## Still Not Working?

### Get Detailed Debug Info

Run this in browser console:
```javascript
console.log({
  searchInput: !!document.getElementById('searchInput'),
  autocompleteDropdown: !!document.getElementById('autocompleteDropdown'),
  autocompleteList: !!document.getElementById('autocompleteList'),
  searchForm: !!document.getElementById('searchForm'),
  fetchAutocomplete: typeof fetchAutocomplete,
  mainJsLoaded: document.querySelector('script[src*="main.js"]') !== null
});
```

Copy the output and check:
- All should be `true` except `fetchAutocomplete` which should be `"undefined"` (it's in a closure)
- If any is `false`, that's your issue

### Share Debug Output
If still stuck, provide:
1. Browser console output (all messages)
2. Network tab output (for /api/autocomplete/ request)
3. Django server logs
4. Result of debug info above
