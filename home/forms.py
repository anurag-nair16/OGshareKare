from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import Donation,Volunteer,NGO, NGOProfile, Product, CreateCampaign, Donor

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','first_name', 'email','password1','password2']

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['location']


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['other_products', 'phone_number', 'product_images', 'product_quantity']
        
class VolunteerForm(forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = ['fullname', 'email', 'phone', 'location', 'address', 'availability', 'interests', 'message']
        widgets = {
            'interests': forms.CheckboxSelectMultiple(),  # Render interests field as checkboxes
            'message': forms.Textarea(attrs={'rows': 4, 'cols': 100}),  # Set textarea attributes
        }


class NGORegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    regno = forms.CharField()
    ngoname = forms.CharField()
    document = forms.FileField()

    def save(self, commit=True):
        user = super(NGORegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            profile = NGO.objects.create(
                user=user,
                regno=self.cleaned_data['regno'],
                ngoname=self.cleaned_data['ngoname'],
                document=self.cleaned_data['document']
            )
        return user
    
class NGOProfileForm(forms.ModelForm):
    class Meta:
        model = NGOProfile
        fields = ['location', 'address', 'description', 'image1']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['productName', 'quantity', 'size', 'description']


class CampaignForm(forms.ModelForm):
    class Meta:
        model = CreateCampaign
        fields = ['title', 'description', 'start_date', 'end_date', 'items_needed']

class MarkAsReadForm(forms.Form):
    notification_id = forms.IntegerField(widget=forms.HiddenInput())