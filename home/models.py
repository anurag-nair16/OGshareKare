from django.db import models
from django.contrib.auth.models import User,AbstractUser

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    other_products = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    product_quantity = models.IntegerField()
    product_images = models.ImageField(upload_to="images/")

    def __str__(self):
        return f"Donation by {self.contact_name}"

class Volunteer(models.Model):
    fullname = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.BigIntegerField()
    address = models.CharField(max_length=255, blank=True, null=True)
    AVAILABILITY_CHOICES = [
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
        ('Both', 'Both'),
    ]
    availability = models.CharField(max_length=8, choices=AVAILABILITY_CHOICES)
    interests = models.CharField(max_length=255) 
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.fullname
    

class NGO(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    regno = models.CharField(max_length=255)
    ngoname = models.CharField(max_length=255)
    document = models.FileField(upload_to='ngo_documents/')
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
class NGOProfile(models.Model):
    ngo = models.OneToOneField(NGO, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255)  # Added address field
    description = models.TextField()
    image1 = models.ImageField(upload_to='images/')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.ngo.ngoname

    

class Product(models.Model):
    productName = models.CharField(max_length=255)
    quantity = models.IntegerField()
    size = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField()
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE)

    def __str__(self):
        return f"Donation asked by {self.ngo.ngoname}"
    

class CreateCampaign(models.Model):
    
    ngo = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    items_needed = models.TextField()  # List of items needed

    def __str__(self):
        return self.title