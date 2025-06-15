
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='buyer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=100)
    farm_location = models.CharField(max_length=200)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Size in acres")
    certification = models.CharField(max_length=100, blank=True, help_text="Organic certification, etc.")
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.farm_name} - {self.user.username}"

class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    company_name = models.CharField(max_length=100, blank=True)
    buyer_type = models.CharField(max_length=50, choices=[
        ('individual', 'Individual'),
        ('restaurant', 'Restaurant'),
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
    ], default='individual')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_buyer_type_display()}"