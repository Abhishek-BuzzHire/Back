from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin): # <-- Inherit from AbstractBaseUser and PermissionsMixin
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    
    # Required fields for AbstractBaseUser compatibility
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True) # Essential for login
    is_superuser = models.BooleanField(default=False) # Inherited from PermissionsMixin

    # Your custom fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lastlogin = models.DateTimeField(null=True, blank=True)

    # Class attributes required by Django's auth system
    USERNAME_FIELD = 'email'  # <-- The field used for login (e.g., in Simple JWT)
    REQUIRED_FIELDS = ['name'] # <-- Fields required when creating a user via command line
    
    objects = UserManager() # <-- Assign the custom manager

    def __str__(self):
        return self.email

# ===========================
# ATTENDANCE MODEL
# ===========================

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    date = models.DateField(auto_now_add=True)
    
    punch_in_time = models.DateTimeField(null=True, blank=True)
    punch_out_time = models.DateTimeField(null=True, blank=True)

    punch_in_lat = models.FloatField(null=True, blank=True)
    punch_in_lon = models.FloatField(null=True, blank=True)

    punch_out_lat = models.FloatField(null=True, blank=True)
    punch_out_lon = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} | {self.punch_in_time}"
