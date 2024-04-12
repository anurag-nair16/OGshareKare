from django.contrib import admin

# Register your models here.
from .models import Donation,Volunteer,NGO, NGOProfile, Product, CreateCampaign, Donor

admin.site.register(Donation)
admin.site.register(Volunteer)
admin.site.register(NGOProfile)
admin.site.register(NGO)
admin.site.register(Product)
admin.site.register(CreateCampaign)
admin.site.register(Donor)


