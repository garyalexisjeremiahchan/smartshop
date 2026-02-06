# Dynamic Product Descriptions - Quick Start Guide

## What Is This?

The Dynamic Product Descriptions feature automatically generates engaging, sales-focused product descriptions using AI. It transforms basic product information into compelling copy that helps convert browsers into buyers.

## Example Transformation

**Before (Original):**
> Comfortable flip flop sandals

**After (AI-Generated):**
> Step into comfort with our Women's Flip Flops, where everyday ease meets beach-ready style. Featuring a soft yoga mat footbed and supportive arch design, these lightweight sandals cradle your feet from morning strolls to sun-soaked afternoons. Customers rave about their all-day comfort, making them the perfect companion for any casual outing. Available in colors that match your vibrant lifestyle, these flip flops are a must-have for your summer wardrobe. Treat your feet to the comfort they deserve—grab your pair today!

## How It Works

1. **User visits a product page** → System checks if description needs updating
2. **If needed** → AI generates new description using OpenAI API
3. **Description saved** → Stored in database for 7 days
4. **Displayed on page** → Shown prominently with original details available in collapsible section

## Setup (Already Done! ✓)

✓ Database fields added
✓ OpenAI API integrated
✓ Views updated
✓ Templates modified
✓ Migrations applied

## Configuration Required

Add to your `.env` file (if not already present):

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

## Usage

### Automatic (Default Behavior)

Just visit any product page - the system automatically:
- Checks if description needs generation
- Generates if needed (first visit or >7 days old)
- Displays the AI description

### Manual Generation

Generate for specific product:
```bash
python manage.py generate_dynamic_descriptions --product-id 1768
```

Generate for multiple products (limit 10):
```bash
python manage.py generate_dynamic_descriptions --limit 10
```

Force regeneration (even if fresh):
```bash
python manage.py generate_dynamic_descriptions --product-id 1768 --force
```

Generate for all products:
```bash
python manage.py generate_dynamic_descriptions
```

### Testing

Run the test suite:
```bash
python test_dynamic_descriptions.py
```

## Where to See It

1. Visit any product detail page (e.g., `/product/flip-flops-women-comfort/`)
2. Look for the "Product Description" section
3. You'll see:
   - **AI-Enhanced Description** (main display with gradient card)
   - **Technical Details** (collapsible accordion with original description)

## Customization

### Change AI Model

In `.env`:
```bash
OPENAI_MODEL=gpt-4  # More expensive but better quality
OPENAI_MODEL=gpt-3.5-turbo  # Faster and cheaper
OPENAI_MODEL=gpt-4o-mini  # Default - good balance
```

### Adjust Regeneration Frequency

Edit `store/dynamic_description.py`, line ~35:
```python
# Change from 7 days to 30 days
one_week_ago = timezone.now() - timedelta(days=30)
```

### Modify Prompt Style

Edit the prompt in `store/dynamic_description.py`, method `_build_prompt()` (line ~50)

## What Gets Analyzed?

The AI considers:
- Product name, category, price
- Original description
- Product specifications
- Customer reviews (up to 10 most recent)
- Units sold (social proof)

## Performance

- **First visit**: ~2-3 seconds (includes API call)
- **Subsequent visits**: <100ms (reads from database)
- **Cost per description**: ~$0.0001-0.0003 (with gpt-4o-mini)
- **Cache duration**: 7 days or until product is updated

## Troubleshooting

### No description generated?

Check:
1. Is `OPENAI_API_KEY` set in .env?
2. Is the API key valid?
3. Check Django logs for errors
4. Test manually: `python manage.py generate_dynamic_descriptions --product-id [ID]`

### Description too short/long?

Edit `store/dynamic_description.py`, line ~125:
```python
max_tokens=300,  # Increase for longer descriptions
```

### Want to disable the feature temporarily?

Comment out these lines in `store/views.py` (around line 116):
```python
# description_generator = DynamicDescriptionGenerator()
# if description_generator.needs_regeneration(product):
#     description_generator.update_product_description(product)
#     product.refresh_from_db()
```

## Files Modified/Created

1. **store/models.py** - Added fields to Product model
2. **store/dynamic_description.py** - Core generator class (NEW)
3. **store/views.py** - Updated product_detail view
4. **templates/store/product_detail.html** - Updated UI
5. **store/management/commands/generate_dynamic_descriptions.py** - Management command (NEW)
6. **store/migrations/0005_*.py** - Database migration (NEW)

## Next Steps

1. **Generate descriptions for existing products:**
   ```bash
   python manage.py generate_dynamic_descriptions --limit 10
   ```

2. **Visit a product page to see the result**

3. **Monitor and adjust** based on results

4. **Optional**: Set up monitoring for API costs in OpenAI dashboard

## Support

- Full documentation: `DYNAMIC_DESCRIPTION_DOCUMENTATION.md`
- Test suite: `python test_dynamic_descriptions.py`
- Django logs: Check terminal output when running `python manage.py runserver`

## Tips

- Start with `--limit` flag to test on few products first
- Monitor OpenAI costs in your OpenAI dashboard
- The AI learns from reviews - better reviews = better descriptions
- Descriptions improve as you get more customer reviews
- Use `--force` flag to regenerate if you're not happy with a description
