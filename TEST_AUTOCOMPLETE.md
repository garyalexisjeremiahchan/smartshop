# Quick Autocomplete Test

## Method 1: Browser Console Test (Easiest)

1. **Go to your site**: http://127.0.0.1:8000/
2. **Open Developer Console**: Press F12
3. **Paste this code** into the Console tab and press Enter:

```javascript
// Test if elements exist
console.log('searchInput:', document.getElementById('searchInput'));
console.log('autocompleteDropdown:', document.getElementById('autocompleteDropdown'));
console.log('autocompleteList:', document.getElementById('autocompleteList'));

// If all are found, test the autocomplete manually
const dropdown = document.getElementById('autocompleteDropdown');
const list = document.getElementById('autocompleteList');

if (dropdown && list) {
    // Fetch suggestions
    fetch('/api/autocomplete/?q=lap')
        .then(r => r.json())
        .then(data => {
            console.log('API Response:', data);
            
            // Clear list
            list.innerHTML = '';
            
            // Add suggestions
            data.suggestions.forEach(suggestion => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="bi bi-search me-2"></i><span>${suggestion}</span>`;
                li.style.padding = '0.75rem 1rem';
                li.style.cursor = 'pointer';
                li.style.borderBottom = '1px solid #f0f0f0';
                li.addEventListener('click', () => {
                    document.getElementById('searchInput').value = suggestion;
                    dropdown.style.display = 'none';
                });
                list.appendChild(li);
            });
            
            // Show dropdown
            dropdown.style.display = 'block';
            console.log('✓ Dropdown should now be visible!');
        });
} else {
    console.error('Elements not found!');
}
```

**What to look for:**
- If dropdown appears → JavaScript works, just need to attach event listener
- If dropdown doesn't appear → CSS or positioning issue
- If you get errors → Element IDs don't match

---

## Method 2: Check Console Messages

1. Go to: http://127.0.0.1:8000/
2. Press F12 → Console tab
3. Type "lap" in the search bar
4. Look for these messages:

**✅ Working:**
```
AI Search autocomplete initialized successfully
Search input: lap
Fetching autocomplete for: lap
Received suggestions: [...]
```

**❌ Not Working:**
- No messages = JavaScript not loading
- "element not found" = Template issue
- "Autocomplete error" = API issue (but we know API works)

---

## Method 3: Check if JavaScript File Loaded

1. Press F12 → Sources tab
2. Navigate to: static → js → main.js
3. Press Ctrl+F and search for: "fetchAutocomplete"
4. If found → File is loaded
5. If not found → Old cached version

**Fix:** Hard refresh with Ctrl+Shift+R

---

## Quick Fix Checklist

If autocomplete isn't showing:

### 1. Hard Refresh Browser
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### 2. Clear Browser Cache
- Chrome: F12 → Right-click refresh button → "Empty Cache and Hard Reload"
- Firefox: Ctrl+Shift+Delete → Clear Cache
- Any browser: Open in Incognito/Private mode

### 3. Verify JavaScript Loaded
In console, run:
```javascript
console.log(document.querySelector('script[src*="main.js"]').src);
```
Should show the path to main.js

### 4. Check Event Listeners
In console, run:
```javascript
const input = document.getElementById('searchInput');
console.log('Has input listener:', !!input.oninput || getEventListeners(input).input?.length > 0);
```

---

## Common Issues

### Issue: "Dropdown doesn't appear"
**Cause:** CSS display:none not being removed
**Test:** Run in console:
```javascript
document.getElementById('autocompleteDropdown').style.display = 'block';
```
If it appears, JavaScript isn't calling `displayAutocomplete()`

### Issue: "No console messages"
**Cause:** JavaScript file not loaded or wrong version
**Fix:** 
1. Ctrl+Shift+R to hard refresh
2. Check Network tab for main.js (should be 200 status)
3. View main.js source and verify it has autocomplete code

### Issue: "Elements not found"
**Cause:** Wrong page or template
**Fix:** Make sure you're on a page that uses base.html (like home page)

---

## What to Report Back

Run this complete diagnostic and tell me the results:

```javascript
// Complete diagnostic
console.log('=== AUTOCOMPLETE DIAGNOSTIC ===');
console.log('1. Search input exists:', !!document.getElementById('searchInput'));
console.log('2. Dropdown exists:', !!document.getElementById('autocompleteDropdown'));
console.log('3. List exists:', !!document.getElementById('autocompleteList'));
console.log('4. Form exists:', !!document.getElementById('searchForm'));
console.log('5. Main.js loaded:', !!document.querySelector('script[src*="main.js"]'));

// Try to show dropdown manually
const dd = document.getElementById('autocompleteDropdown');
if (dd) {
    dd.style.display = 'block';
    dd.style.background = 'yellow';
    dd.innerHTML = '<div style="padding:20px">TEST - Can you see this?</div>';
    console.log('6. Dropdown should now have yellow background and show "TEST"');
} else {
    console.log('6. ERROR: Dropdown element not found');
}
console.log('===============================');
```

Copy the console output and send it to me!
