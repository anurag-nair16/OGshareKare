from django.db import models
from django.contrib.auth.models import User,AbstractUser
from math import radians, sin, cos, sqrt, atan2
from django.urls import reverse
from django.utils.safestring import mark_safe   
from django.utils.timezone import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from icalendar import Calendar, Event
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, null=True, blank=True)
    other_products = models.TextField(max_length=100)
    phone_number = models.CharField(max_length=15)
    product_quantity = models.IntegerField()
    product_images = models.ImageField(upload_to="images/")
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DONATED', 'Donated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Donation by {self.user.first_name}"

class Volunteer(models.Model):
    fullname = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.BigIntegerField()
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    AVAILABILITY_CHOICES = [
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
        ('Both', 'Both'),
    ]
    availability = models.CharField(max_length=8, choices=AVAILABILITY_CHOICES)
    interests = models.CharField(max_length=255) 
    message = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.fullname
    

class NGO(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    regno = models.CharField(max_length=255)
    ngoname = models.CharField(max_length=255)
    document = models.FileField(upload_to='ngo_documents/')
    is_verified = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
class NGOProfile(models.Model):
    ngo = models.OneToOneField(NGO, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255)  # Added address field
    description = models.TextField()
    image1 = models.ImageField(upload_to='images/')
    
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
    items_needed = models.TextField()  
    location = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Set the location of the campaign to be the same as the location of the NGO
        print('hello')
        self.ngop = NGO.objects.get(user=self.ngo)
        print(self.ngop.ngoprofile.location)
        if self.ngo and not self.location:
            self.location = self.ngop.ngoprofile.location  # Assuming the location field exists in the User model
        super(CreateCampaign, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def send_campaign_invites(self):
        # Fetch all donors
        print(self.ngo)
        ngol = NGO.objects.get(user=self.ngo)
        print(ngol)
        donors = Donor.objects.all()
        ngo_latitude = ngol.latitude
        ngo_longitude = ngol.longitude

        for donor in donors:
            donor_latitude = donor.latitude
            donor_longitude = donor.longitude
            # Calculate distance between donor and NGO using Haversine formula
            distance = self.haversine_distance(
                ngo_latitude, ngo_longitude, donor_latitude, donor_longitude
            )

            if distance <= 75:
                self.send_calendar_invite(donor.user.email)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371 * c  # Radius of Earth in kilometers
        return distance

    def send_calendar_invite(self, recipient_email):
        print(recipient_email)
        subject = f"Invitation: {self.title}"
        from_email = "anurag.nair22@spit.ac.in"  # Change this to your email address
        to_email = [recipient_email]
        
        # Render HTML content for the email
        html_content = render_to_string('email/calendar_invite.html', {
            'title': self.title,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
        })

        # Convert HTML content to plain text
        text_content = strip_tags(html_content)

        cal = Calendar()
        cal.add('prodid', '-//EdaMone//ShareKare//EN')
        cal.add('version', '2.0')

        event = Event()
        event.add('summary', self.title)
        event.add('dtstart', self.start_date)
        event.add('dtend', self.end_date + timedelta(days=1))  # Add a day to include end date
        event.add('description', self.description)
        # Add other event details like location, etc., if needed

        cal.add_component(event)
        ics_content = cal.to_ical()

        # Send email with both HTML and plain text content
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.attach('event.ics', ics_content, 'text/calendar')
        email.send()

@receiver(post_save, sender=CreateCampaign)
def send_campaign_invites(sender, instance, created, **kwargs):
    if created:  # Only send invites if a new campaign was created
        instance.send_campaign_invites()
    
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        self.read = True
        self.save()

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371 * c  # Radius of Earth in kilometers
        return distance

    @staticmethod
    def send_campaign_notifications(ngo_instance):
        # Fetch all donors
        donors = Donor.objects.all()
        ngo_latitude = ngo_instance.ngo.latitude
        ngo_longitude = ngo_instance.ngo.longitude

        notified_donors = set()

        for donor in donors:
            donor_latitude = donor.latitude
            donor_longitude = donor.longitude
            # Calculate distance between donor and NGO using Haversine formula
            distance = Notification.haversine_distance(
                ngo_latitude, ngo_longitude, donor_latitude, donor_longitude
            )

            if distance <= 75 and donor.user.id not in notified_donors:
                url = reverse('ngo_donations', kwargs={'ngo_id': ngo_instance.ngo.id, 'don_id': 1})
                url+='#campaigns'
                message = mark_safe(f"A new campaign has been created near you by '{ngo_instance.ngo.ngoname}'! <a href='{url}'>Click here</a> for more details.")
                Notification.objects.create(
                    user=donor.user,
                    message=message
                )
                notified_donors.add(donor.user.id)