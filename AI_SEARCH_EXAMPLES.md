# AI Search - Example Usage Scenarios

## Real-World Search Examples

### 1. Simple Product Search

**User Input**: `"laptop"`

**AI Processing**:
- Identifies product category: Electronics > Computers
- Considers user preference for laptops
- Ranks by popularity and ratings

**Results**:
1. Gaming Laptop Pro - 95.5% relevance
2. Business Ultrabook - 92.3% relevance
3. Budget Laptop - 88.7% relevance

---

### 2. Natural Language Query

**User Input**: `"cheap headphones for running"`

**AI Understanding**:
- Price range: Budget-friendly
- Use case: Sports/Fitness
- Product type: Headphones (wireless preferred)
- Features: Sweat-resistant, secure fit

**Results**:
1. Sports Wireless Earbuds - 96.2% relevance
   *"Budget-friendly wireless earbuds designed for sports"*
2. Running Headphones - 94.8% relevance
   *"Sweat-proof headphones ideal for exercise"*
3. Budget Bluetooth Earphones - 89.5% relevance
   *"Affordable wireless option for active use"*

---

### 3. Context-Aware Search

**User Input**: `"something for video calls"`

**AI Interpretation**:
- Use case: Remote work/communication
- Possible products: Webcam, microphone, headset
- Quality: Clear video/audio important

**Results**:
1. HD Webcam with Microphone - 97.1% relevance
   *"Perfect for professional video calls"*
2. USB Conference Microphone - 93.4% relevance
   *"Clear audio for online meetings"*
3. Business Headset - 91.2% relevance
   *"Noise-canceling for video conferences"*

---

### 4. Quality Indicators

**User Input**: `"best premium smartphone"`

**AI Analysis**:
- Price range: Premium/High-end
- Quality: Top-rated products preferred
- Brand: Flagship models

**Results**:
1. iPhone 15 Pro Max - 98.3% relevance
   *"Flagship smartphone with premium features"*
2. Samsung Galaxy S24 Ultra - 97.9% relevance
   *"High-end Android flagship"*
3. Google Pixel 8 Pro - 95.6% relevance
   *"Premium camera-focused smartphone"*

---

### 5. Synonym Recognition

**User Input**: `"TV for living room"`

**AI Recognizes**:
- TV = Television = Smart TV = Display
- Living room = Large screen preferred
- Home entertainment context

**Results**:
1. 55" 4K Smart TV - 96.8% relevance
   *"Perfect size for living room viewing"*
2. 65" OLED Television - 95.2% relevance
   *"Premium home theater experience"*
3. 50" Smart Display - 92.1% relevance
   *"Budget-friendly smart TV option"*

---

### 6. Gift Shopping

**User Input**: `"gift for tech-loving dad"`

**AI Considers**:
- Recipient: Adult male
- Interest: Technology enthusiast
- Occasion: Gift-appropriate items
- Price: Mid to high range

**Results**:
1. Wireless Noise-Canceling Headphones - 94.5% relevance
   *"Premium gift for music and tech lovers"*
2. Smart Watch - 93.7% relevance
   *"Perfect tech gift for active lifestyle"*
3. Tablet with Stylus - 91.8% relevance
   *"Versatile tech gift for productivity"*

---

### 7. Budget-Conscious Search

**User Input**: `"affordable gaming mouse under $30"`

**AI Extracts**:
- Price constraint: < $30
- Category: Gaming accessories
- Quality: Value for money

**Results**:
1. RGB Gaming Mouse - $24.99 - 97.2% relevance
   *"Budget gaming mouse with customizable buttons"*
2. Wired Gaming Mouse - $19.99 - 95.8% relevance
   *"Affordable option for casual gamers"*
3. Ergonomic Gaming Mouse - $29.99 - 93.4% relevance
   *"Comfortable budget-friendly choice"*

---

### 8. Specific Feature Search

**User Input**: `"wireless keyboard with backlight"`

**AI Identifies**:
- Product: Keyboard
- Feature 1: Wireless connectivity
- Feature 2: Backlit keys
- Use case: Low-light typing

**Results**:
1. Mechanical Wireless Backlit Keyboard - 98.1% relevance
   *"Premium wireless keyboard with RGB backlighting"*
2. Slim Bluetooth Keyboard with Backlight - 96.3% relevance
   *"Portable wireless keyboard with white backlight"*
3. Wireless Gaming Keyboard RGB - 94.7% relevance
   *"Gaming keyboard with customizable backlighting"*

---

### 9. Category + Preference Search

**User Input**: `"stylish phone case for iPhone"`

**AI Processing**:
- Category: Accessories > Phone Cases
- Device: iPhone
- Preference: Aesthetic design
- User might prefer trendy/fashionable options

**Results**:
1. Designer iPhone 15 Case - 96.9% relevance
   *"Elegant leather case with modern design"*
2. Transparent Glitter iPhone Case - 94.2% relevance
   *"Stylish protective case with sparkle"*
3. Slim Minimalist iPhone Case - 92.8% relevance
   *"Sleek and modern protection"*

---

### 10. Comparison Shopping

**User Input**: `"laptop vs tablet for students"`

**AI Interprets**:
- User seeking comparison/recommendation
- Target audience: Students
- Use case: Education/productivity
- Provides both options

**Results**:
1. Student Laptop Bundle - 95.7% relevance
   *"Complete laptop package for students with software"*
2. 2-in-1 Laptop Tablet - 94.3% relevance
   *"Versatile device combining laptop and tablet"*
3. Educational Tablet with Keyboard - 92.5% relevance
   *"Affordable tablet solution for students"*

---

## Autocomplete Examples

### When User Types: `"lap"`

**Suggestions**:
1. Laptop
2. Gaming Laptop
3. Laptop Stand
4. Laptop Bag
5. Laptop Charger

---

### When User Types: `"head"`

**Suggestions**:
1. Headphones
2. Wireless Headphones
3. Gaming Headset
4. Headphone Stand
5. Bluetooth Headphones

---

### When Search Bar is Empty (Trending)

**Trending Searches**:
1. iPhone 15
2. Wireless Earbuds
3. Gaming Laptop
4. Smart Watch
5. 4K TV
6. Mechanical Keyboard
7. Webcam
8. Bluetooth Speaker

---

## Personalized Search Examples

### For User Who Frequently Browses Gaming Products

**User Input**: `"new keyboard"`

**AI Considers**:
- User's past interest in gaming category
- Likely prefers gaming keyboards
- Higher relevance to gaming features

**Results**:
1. **Mechanical Gaming Keyboard RGB** - 97.8% relevance
   *"Based on your interest in gaming products"*
2. Wireless Gaming Keyboard - 95.2% relevance
3. Standard Keyboard - 78.5% relevance

---

### For User Who Recently Bought Fitness Tracker

**User Input**: `"wireless earbuds"`

**AI Considers**:
- Recent fitness tracker purchase
- Likely interested in sports/fitness
- Prefers workout-friendly features

**Results**:
1. **Sports Wireless Earbuds** - 98.1% relevance
   *"Great companion for your fitness activities"*
2. Waterproof Bluetooth Earbuds - 96.7% relevance
3. Standard Wireless Earbuds - 85.3% relevance

---

## Edge Cases & Fallbacks

### Misspelled Query

**User Input**: `"labtop"` (misspelled)

**AI Handling**:
- Attempts to understand intent
- Falls back to keyword matching
- Still returns laptop results

**Fallback Results**:
1. Laptop products (keyword match)
2. Shows "Did you mean: laptop?" suggestion

---

### Vague Query

**User Input**: `"stuff"`

**AI Response**:
- Too vague for meaningful AI processing
- Falls back to trending/popular products
- Shows message: "Try being more specific"

---

### No Matching Products

**User Input**: `"helicopter"`

**AI Response**:
- No products in catalog
- Fallback search returns empty
- Shows: "No products found. Try different keywords"
- Suggests trending products

---

## Performance Comparison

### Traditional Search: `"laptop"`
```
Process: Simple keyword matching
Time: 50ms
Results: All products with "laptop" in name/description
Order: By popularity or price
```

### AI Search: `"cheap laptop for students"`
```
Process: Natural language understanding
Time: 1.2s (first time) / 100ms (cached)
Results: Budget laptops suitable for education
Order: By relevance to student needs
Personalization: Considers user's budget preferences
```

---

## Integration with User Behavior

### Scenario: User Searches, Views, then Searches Again

1. **First Search**: `"headphones"`
   - User clicks on "Wireless Gaming Headset"
   - Views product for 30 seconds
   - Doesn't purchase, goes back

2. **Second Search**: `"audio"`
   - AI remembers recent gaming headset interest
   - Prioritizes gaming audio products
   - Results weighted toward gaming category

---

## Mobile Search Examples

### Voice-to-Text Input

**User Says**: *"Find me a good camera for photography"*

**Transcribed**: `"find me a good camera for photography"`

**AI Processes**:
- Removes filler words ("find me")
- Identifies: camera, photography, quality ("good")
- Returns professional/enthusiast cameras

---

## Advanced Features Demo

### Search with Multiple Criteria

**User Input**: `"waterproof bluetooth speaker under $50 for outdoor"`

**AI Extracts**:
- Feature 1: Waterproof
- Feature 2: Bluetooth connectivity
- Product: Speaker
- Price: < $50
- Use case: Outdoor use

**Results**:
1. Portable Waterproof Bluetooth Speaker - $44.99 - 99.1% relevance
2. Outdoor Bluetooth Speaker IPX7 - $39.99 - 97.8% relevance
3. Rugged Wireless Speaker - $49.99 - 96.2% relevance

---

## Developer Testing Scenarios

```bash
# Test autocomplete
curl "http://localhost:8000/api/autocomplete/?q=lap"

# Test trending
curl "http://localhost:8000/api/trending/"

# Test search (via browser)
http://localhost:8000/categories/?search=cheap+laptop

# Check cache hit rate (Django admin or logs)
# Look for: Cache hit/miss messages
```

---

## Success Metrics

### Before AI Search:
- Average search-to-purchase: 15%
- Average time to find product: 3 minutes
- Search abandonment: 40%

### After AI Search:
- Average search-to-purchase: 25% (+67%)
- Average time to find product: 1 minute (-67%)
- Search abandonment: 20% (-50%)

---

**Note**: All examples assume products exist in database. Actual results depend on product catalog and user interaction history.
