import requests
from django.shortcuts import render, redirect
from .forms import CreateUserForm,DonationForm,VolunteerForm,NGORegistrationForm, NGOProfileForm, ProductForm, CampaignForm, DonorForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import User, Donation, NGO, NGOProfile, Product, CreateCampaign, Donor
from django.utils import timezone
import math
from django.conf import settings
from django.core.cache import cache

def home(request):
    return render(request,'index.html',{})

def real_campaigns(request):
    camp = CreateCampaign.objects.all()
    prof = NGOProfile.objects.filter(ngo=campaign.ngo)
    context = {
        'camp':camp,
        'prof':profile
    }
    
    return render(request,'realcampaigns.html',context)

def create_donation(request):

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.ngo_id = request.user.ngo.id
            product.save()
            messages.success(request, 'Product succesfully added ')
            return redirect('ngo_dashboard')  
        else:
            messages.error(request,'There was an issue. Please try again')
    else:
        form = ProductForm()

    return render(request,'create_donation.html',{})

@login_required
def user_donation(request, user_id, product_id):
    donor = User.objects.get(id=user_id)
    donations = Donation.objects.filter(user_id=donor)
    
    product_high = Donation.objects.get(id=product_id)
    
    context = {
        'donor': donor,
        'donations': donations,
        'product_high': product_high
    }
    
    return render(request, 'user_donation.html', context)


@login_required(login_url='login')
def ngo_dash(request):

    if request.user.is_authenticated:
        try:
            profile = NGO.objects.get(user=request.user)
            if not profile.ngoname:
                messages.error(request, 'Donors are not allowed to access this page.')
                return redirect('home')
        except NGO.DoesNotExist:
            messages.error(request, 'Donors are not allowed to access this page.')
            return redirect('home') 

    profile = NGO.objects.get(user=request.user)
    

    query = request.GET.get('q')
    donation = Donation.objects.filter(other_products__icontains=query) if query else Donation.objects.all()
    

    context = {
        'ngoname': profile.ngoname,
        'regno': profile.regno,
        'donation': donation
    }

    return render(request,'ngo_dashboard.html',context)


def ngo_donations(request, ngo_id, don_id):
    ngo = NGO.objects.get(id=ngo_id)
    donations = Product.objects.filter(ngo=ngo)
    
    product_high = Product.objects.get(id=don_id)

    user = ngo.user

    active_campaigns = CreateCampaign.objects.filter(ngo=user, start_date__lte=timezone.now(), end_date__gte=timezone.now())
    
    upcoming_campaigns = CreateCampaign.objects.filter(ngo=user, start_date__gt=timezone.now())

    context = {
        'ngo': ngo,
        'donations': donations,
        'product_high': product_high,
        'active_campaigns': active_campaigns,
        'upcoming_campaigns': upcoming_campaigns
    }

    return render(request, 'ngo_donations.html', context)


def get_lat_lon_from_location(location_name):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={location_name}, India"
    response = requests.get(url)
    data = response.json()
    
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    else:
        return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    r = 6371  # Radius of the earth in kilometers
    return round(r * c, 2)


def main_home(request):
    query = request.GET.get('q')
    products = Product.objects.filter(productName__icontains=query) if query else Product.objects.all()

    nearest_campaigns = []

    if request.user.is_authenticated:
        try:
            profile = Donor.objects.get(user=request.user)
            user_location_name = profile.location
            if not profile.latitude and not profile.longitude:
                user_lat, user_lon = get_lat_lon_from_location(user_location_name)
            else:
                user_lat=profile.latitude
                user_lon=profile.longitude

            if user_lat and user_lon:
                profile.latitude = user_lat
                profile.longitude = user_lon
                profile.save()

                for product in products:
                    ngo_location = product.ngo.ngoprofile.location
                    if not product.ngo.ngoprofile.latitude and not product.ngo.ngoprofile.longitude:
                        ngo_lat, ngo_lon = get_lat_lon_from_location(ngo_location)
                    else:
                        ngo_lat=product.ngo.ngoprofile.latitude
                        ngo_lon=product.ngo.ngoprofile.longitude
                    if ngo_lat and ngo_lon:
                        try:
                            product.ngo.ngoprofile.latitude = ngo_lat
                            product.ngo.ngoprofile.longitude = ngo_lon
                            product.ngo.ngoprofile.save()
                        except Exception as e:
                            print(f"Error calculating distance: {e}")

                products = sorted(products, key=lambda x: haversine_distance(user_lat, user_lon, x.ngo.ngoprofile.latitude, x.ngo.ngoprofile.longitude))

                context = {'products': products, 'nearest_campaigns': nearest_campaigns}
                return render(request, 'home.html', context)
            
        except Donor.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error fetching user location: {e}")

    context = {'products': products, 'nearest_campaigns': nearest_campaigns}
    return render(request, 'home.html', context)


def signup(request):
    form = CreateUserForm()
    donor_form = DonorForm()  # Add DonorForm instance

    if request.user.is_authenticated:
        return redirect('campaign')
    else:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            donor_form = DonorForm(request.POST)  # Handle DonorForm
            if form.is_valid() and donor_form.is_valid():
                user = form.save()
                donor = donor_form.save(commit=False)
                donor.user = user
                donor.save()
                messages.success(request, 'Account created successfully')
                return redirect('login')
        
        context = {'form': form, 'donor_form': donor_form}  # Add donor_form to context
        return render(request, 'signup.html', context)
    
def joinus(request):
    if request.method == "POST":
        form = VolunteerForm(request.POST or None)
        if form.is_valid():
            fullname=request.POST['fullname']
            form.save()
            messages.success(request,(f'Thank you {fullname}. Your response has been recorded. We will contact you soon!'))
            return redirect('joinus')
        else:
            form = VolunteerForm()
            messages.error(request, 'There was an error processing your form.')
    else:
        return render(request,'joinus.html',{})


@login_required(login_url='login')
def campaign(request):
    form = DonationForm()
    user_donations = Donation.objects.filter(user=request.user)

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.user = request.user
            donation.save()
            form = DonationForm() 
            messages.success(request, 'Donation form submitted succesfully')
        else:
            form_errors = form.errors
            print(request.POST)
            print(request.FILES)
            return render(request, 'campaign.html', {'form': form, 'user_donations': user_donations, 'form_errors': form_errors})

    return render(request, 'campaign.html', {'form': form, 'user_donations': user_donations})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')  

def register_ngo(request):
    if request.method == 'POST':
        form = NGORegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = request.POST.get('username')
            if username.endswith("_ngo"):
                form.save()
                messages.success(request,'Account created succesfully! Please wait for verification')
                return redirect('login')
            else:
                messages.error(request,'Username must end with \'_ngo\'')
    else:
        form = NGORegistrationForm()
    return render(request, 'register_ngo.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if username.endswith("_ngo"):
                try:
                    profile = NGO.objects.get(user=user)
                    if profile.is_verified:
                        login(request, user)
                        return redirect('ngo_details')
                    else:
                        messages.error(request, 'Account is not verified.')
                except NGO.DoesNotExist:
                    messages.error(request, 'User profile does not exist.')
            else:  
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, 'Invalid login details. Check your username and password.')
    
    return render(request, 'login.html')


@login_required
def profile(request):
    ngo = request.user.ngo
    try:
        profile = NGOProfile.objects.get(ngo=ngo)
        profile_exists = True
    except NGOProfile.DoesNotExist:
        profile_exists = False

    form = None

    if profile_exists:
        return redirect('ngo_dashboard') 
    else:
        if request.method == 'POST':
            form = NGOProfileForm(request.POST, request.FILES)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.ngo = ngo
                profile.save()
                return redirect('ngo_dashboard')  
            else:
                form = NGOProfileForm(instance=profile)

        context = {'form': form}
        return render(request, 'ngodetail.html', context)
    
@login_required
def ngo_profile(request):
    
    ngo = NGO.objects.get(user=request.user)

    ngoprofile = NGOProfile.objects.get(ngo=ngo)
    products = Product.objects.filter(ngo=ngo)
    print(ngo.ngoprofile.address)
    campaigns = CreateCampaign.objects.filter(ngo=request.user,start_date__lte=timezone.now(), end_date__gte=timezone.now())

    context = {
        'ngo': ngo,
        'ngoprofile': ngoprofile,
        'products': products,
        'campaigns':campaigns
    }

    return render(request, 'ngo_profile.html', context)

@login_required
def user_profile(request):
    return render(request, 'userprofile.html')



@login_required
def create_campaign(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.ngo = request.user
            campaign.save()
            messages.success(request, 'Campaign form submitted succesfully')
            return redirect('ngo_dashboard')
    else:
        form = CampaignForm()
    
    return render(request, 'create_campaign.html', {'form': form})
