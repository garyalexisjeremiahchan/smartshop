from django import template

register = template.Library()


@register.inclusion_tag('store/star_rating.html')
def star_rating(rating, show_number=False):
    """
    Display star rating with optional numeric value.
    Rating is rounded to nearest 0.5 for display.
    """
    # Round to nearest 0.5
    rounded_rating = round(rating * 2) / 2
    
    # Calculate full, half, and empty stars
    full_stars = int(rounded_rating)
    half_star = (rounded_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    return {
        'rating': rating,
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),
        'show_number': show_number,
    }


@register.filter
def mask_username(username):
    """
    Mask username showing only first and last character.
    Example: 'admin' becomes 'a***n'
    """
    if not username or len(username) <= 2:
        return username
    
    return f"{username[0]}{'*' * (len(username) - 2)}{username[-1]}"
