from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Register your models here.
from .models import Donation,Volunteer,NGO, NGOProfile, Product, CreateCampaign, Donor

admin.site.register(Donation)
admin.site.register(Volunteer)

class NGOAdmin(admin.ModelAdmin):
    list_display = ('ngoname', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('ngoname', 'user__username')

    def save_model(self, request, obj, form, change):
        print('save_model method called')  # Debugging statement

        original_obj = NGO.objects.get(pk=obj.pk) if change else None

        # Check if is_verified has changed and now is True
        if change and obj.is_verified and not original_obj.is_verified:
            print('is_verified has been changed to True')  # Debugging statement
            
            # Send email to the NGO
            subject = 'Your NGO has been verified'
            
            # Email template
            context = {
                'ngoname': obj.ngoname,
                'regno': obj.regno,
            }
            message = render_to_string('email/verification.html', context)
            plain_message = strip_tags(message)
            
            from_email = 'anurag.nair22@spit.ac.in'  # Update with your email
            to_email = [obj.user.email]
            
            send_mail(subject, plain_message, from_email, to_email, html_message=message, fail_silently=False)
        else:
            print('is_verified has not been changed or is False')  # Debugging statement

        super().save_model(request, obj, form, change)


admin.site.register(NGOProfile)
admin.site.register(NGO,NGOAdmin)
admin.site.register(Product)
admin.site.register(CreateCampaign)
admin.site.register(Donor)


