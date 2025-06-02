from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

#------------------------------------------------------------------------------
# Product Management System
# Handles product categorization, listings, and image management
# - Categories for organizing products
# - Product details and ownership
# - Multiple product images with primary image support
#------------------------------------------------------------------------------

class Category(models.Model):
    # This model represents a category for products
    # Each product can belong to one category
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    # This model represents a product listed by a user
    # Each product has a title, description, price, and belongs to a category
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorited_by = models.ManyToManyField(
        User,
        related_name='favorite_products',
        blank=True
    )
    is_sold = models.BooleanField(default=False)
    sold_date = models.DateTimeField(null=True, blank=True)
    
    def mark_as_sold(self):
        try:
            if not self.is_sold:
                self.is_sold = True
                self.sold_date = timezone.now()
                
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                price_decimal = Decimal(str(self.price))
                wallet.balance = wallet.balance + price_decimal
                wallet.save()
                
                Transaction.objects.create(
                    wallet=wallet,
                    amount=price_decimal,
                    type='SALE',
                    product=self,
                    description=f"Sale of {self.title}"
                )
                
                self.save()
                return True
            return False
        except Exception as e:
            print(f"Error in mark_as_sold: {e}")
            return False

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class ProductImage(models.Model):
    # This model represents an image associated with a product
    # Each product can have multiple images, with one primary image
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

#------------------------------------------------------------------------------
# User Profile System
# Manages user profiles and automatic profile creation
# - Profile information and pictures
# - Username change tracking
# - Signal handlers for profile creation
#------------------------------------------------------------------------------

class UserProfile(models.Model):
    # This model represents a user profile
    # Each user has a one-to-one relationship with a profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    username_changes = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

#------------------------------------------------------------------------------
# Favorites System
# Handles user's product favorites
# - Tracks user-product favorite relationships
# - Ensures unique favorites per user
#------------------------------------------------------------------------------

class FavoriteProduct(models.Model):
    # This model represents a user's favorite product
    # Each user can have multiple favorite products
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

#------------------------------------------------------------------------------
# Shopping Cart System
# Manages user's shopping cart
# - Tracks items added to cart
# - Ensures unique items per user
#------------------------------------------------------------------------------

class CartItem(models.Model):
    # This model represents an item in a user's shopping cart
    # Each user can have multiple items in their cart
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

#------------------------------------------------------------------------------
# Order Management System
# Handles order processing and tracking
# - Complete order information
# - Shipping details
# - Payment processing
# - Order items tracking
#------------------------------------------------------------------------------

class Order(models.Model):
    # This model represents an order placed by a user
    # Each order contains multiple items and has a status
    COUNTRY_CHOICES = [
        ('GB', 'United Kingdom'),
        ('US', 'United States'),
        ('FR', 'France'),
        ('DE', 'Germany'),
        ('ES', 'Spain'),
        ('IT', 'Italy'),
        ('RO', 'Romania'),
        ('PL', 'Poland'),
        ('NL', 'Netherlands'),
        ('BE', 'Belgium'),
        ('DK', 'Denmark'),
        ('SE', 'Sweden'),
        ('NO', 'Norway'),
        ('FI', 'Finland'),
        ('AT', 'Austria'),
        ('CH', 'Switzerland'),
    ]

    PAYMENT_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='GB')
    zip_code = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='card')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.full_name}"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    # This model represents an item in an order
    # Each order can have multiple items
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

#------------------------------------------------------------------------------
# Financial Management System
# Handles all financial transactions
# - User wallets
# - Transaction tracking
# - Withdrawal processing
#------------------------------------------------------------------------------

class Wallet(models.Model):
    # This model represents a user's wallet
    # Each user has a one-to-one relationship with a wallet
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    class Meta:
        db_table = 'user_wallet'


class Transaction(models.Model):
    # This model represents a financial transaction
    # Each transaction is linked to a wallet and can be of different types
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('DEPOSIT', 'Deposit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.type} - {self.amount} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at']


class Withdrawal(models.Model):
    # This model represents a withdrawal request from a user's wallet
    # Each withdrawal is linked to a wallet and has a status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected')
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    bank_account = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']