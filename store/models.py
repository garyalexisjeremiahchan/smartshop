from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model"""
    SORT_CHOICES = [
        ('popular', 'Popular'),
        ('latest', 'Latest'),
        ('top_sales', 'Top Sales'),
        ('price_low_high', 'Price: Low to High'),
        ('price_high_low', 'Price: High to Low'),
    ]
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    specifications = models.TextField(blank=True, help_text='Product specifications')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0)
    units_sold = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        """Count of approved reviews"""
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Product images - support multiple images per product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class Review(models.Model):
    """Product reviews and ratings"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"


class Cart(models.Model):
    """Shopping cart for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.username}"
        return f"Cart - {self.session_key}"
    
    @property
    def total_price(self):
        """Calculate total cart price"""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_items(self):
        """Count total items in cart"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Individual items in the shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product']
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Order(models.Model):
    """Customer orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Shipping Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=300)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Order Details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import random
            import string
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.order_number = f'ORD-{timestamp}-{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"


class OrderItem(models.Model):
    """Items within an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=300)  # Store product name at time of order
    product_price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price at time of order
    quantity = models.PositiveIntegerField(default=1)
    
    @property
    def subtotal(self):
        """Calculate subtotal for this order item"""
        return self.product_price * self.quantity
    
    def save(self, *args, **kwargs):
        # Store product details at time of order
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_price:
            self.product_price = self.product.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class UserInteraction(models.Model):
    """Track user interactions for analytics and data mining"""
    INTERACTION_TYPES = [
        ('view_category', 'View Category'),
        ('view_product', 'View Product'),
        ('add_to_cart', 'Add to Cart'),
        ('update_cart', 'Update Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_started', 'Checkout Started'),
        ('order_placed', 'Order Placed'),
        ('search', 'Search'),
        ('review_submitted', 'Review Submitted'),
        ('product_favorited', 'Product Favorited'),
    ]
    
    # User information (can be anonymous)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
    session_key = models.CharField(max_length=40, blank=True, help_text='Session ID for anonymous users')
    
    # Interaction details
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Related objects
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
    
    # Additional metadata
    quantity = models.IntegerField(null=True, blank=True, help_text='Quantity for cart operations')
    search_query = models.CharField(max_length=255, blank=True, help_text='Search query text')
    page_url = models.CharField(max_length=500, blank=True, help_text='URL of the page')
    referrer_url = models.CharField(max_length=500, blank=True, help_text='Referrer URL')
    
    # User agent and IP for analysis
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Extra data (JSON field for flexibility)
    extra_data = models.JSONField(null=True, blank=True, help_text='Additional interaction data')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['interaction_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['session_key', '-timestamp']),
            models.Index(fields=['product', '-timestamp']),
        ]
    
    def __str__(self):
        user_id = self.user.username if self.user else f"Session: {self.session_key[:8]}"
        return f"{user_id} - {self.get_interaction_type_display()} at {self.timestamp}"
