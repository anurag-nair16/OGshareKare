import requests
from django.shortcuts import render, redirect
from .forms import CreateUserForm,DonationForm,VolunteerForm,NGORegistrationForm, NGOProfileForm, ProductForm, CampaignForm, DonorForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import User, Donation, NGO, NGOProfile, Product, CreateCampaign, Donor, Volunteer
from django.utils import timezone
import math
from itertools import permutations
from django.http import JsonResponse

from django.shortcuts import render

def view_volunteers(request):
    volunteers = Volunteer.objects.all()

    availability = request.GET.get('availability')
    print(availability)
    if availability:
        if availability != 'Both':
            volunteers =volunteers = volunteers.filter(availability=availability) | volunteers.filter(availability='Both')
        else:    
            volunteers = volunteers.filter(availability=availability)

    interests = request.GET.get('interests')
    if interests:
        volunteers = volunteers.filter(interests__icontains=interests)

    context = {
        'volunteers': volunteers,
        'ngoname': request.user.ngo.ngoname 
    }

    return render(request, 'view_volunteers.html', context)


def collect_donations(request):
    if request.method == 'POST':
        selected_donation_ids = request.POST.getlist('selected_donations')
        selected_donations = Donation.objects.filter(id__in=selected_donation_ids)

        
        if selected_donations.exists():
            # Get donor locations
            donor_locations = [(donation.user.donor.latitude, donation.user.donor.longitude) 
                               for donation in selected_donations if donation.user.donor.latitude and donation.user.donor.longitude]
            
            # Get NGO location
            ngo_location = (request.user.ngo.ngoprofile.latitude, request.user.ngo.ngoprofile.longitude)
            print(ngo_location)
            # Solve TSP
            optimal_route, total_distance = solve_tsp(ngo_location, donor_locations)

            location_names=[]
            for lat,lon in optimal_route:
                location = Donor.objects.filter(latitude=lat, longitude=lon).first()
                location_names.append(location.location)


            print(optimal_route)
            print(location_names)


            
            context = {
                'location_names':location_names,
                'optimal_route': optimal_route,
                'total_distance': total_distance,
            }
            
            return render(request, 'optimized_route.html', context)
    
    donations = Donation.objects.all()

    context = {
        'donations': donations,
    }

    return render(request, 'collect_donations.html', context)

def solve_tsp(start, locations):
    min_distance = float('inf')
    optimal_route = None

    for permutation in permutations(locations):
        distance = 0
        current_location = start

        for loc in permutation:
            distance += haversine_distance(current_location[0], current_location[1], loc[0], loc[1])
            current_location = loc

        distance += haversine_distance(current_location[0], current_location[1], start[0], start[1])

        if distance < min_distance:
            min_distance = distance
            optimal_route = permutation

    return optimal_route, round(min_distance, 2)

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


def home(request):
    return render(request,'index.html',{})

def real_campaigns(request):
    camp = CreateCampaign.objects.filter(end_date__gte=timezone.now())
    
    ngo_profiles = []
    
    for campaign in camp:
        try:
            ngo = NGO.objects.get(user=campaign.ngo)
            ngo_profile = NGOProfile.objects.get(ngo=ngo)
            ngo_profiles.append(ngo_profile)
        except NGOProfile.DoesNotExist:
            pass
    
    context = {
        'camp': camp,
        'ngo_profiles': ngo_profiles,
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
    userr = User.objects.get(id=user_id)
    donor = Donor.objects.get(user=userr)
    donations = Donation.objects.filter(user_id=userr)
    product_high = Donation.objects.get(id=product_id)
    
    context = {
        'userr':userr,
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
    donor_form = DonorForm() 

    if request.user.is_authenticated:
        return redirect('campaign')
    else:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            donor_form = DonorForm(request.POST)  
            if form.is_valid() and donor_form.is_valid():
                user = form.save()
                donor = donor_form.save(commit=False)
                donor.user = user
                location_name = donor_form.cleaned_data['location']
                lat, lon = get_lat_lon_from_location(location_name)
                donor.latitude = lat
                donor.longitude = lon
                donor.save()
                messages.success(request, 'Account created successfully')
                return redirect('login')
        
        context = {'form': form, 'donor_form': donor_form}  
        return render(request, 'signup.html', context)
    
def joinus(request):
    if request.method == "POST":
        form = VolunteerForm(request.POST or None)
        if form.is_valid():
            fullname=request.POST['fullname']
            print(fullname)
            form.save()
            messages.success(request,(f'Thank you {fullname}. Your response has been recorded. NGOs will contact you when required!'))
            return redirect('joinus')
        else:
            form_errors = form.errors
            messages.error(request, 'There was an error processing your form.')
            return render(request,'joinus.html',{'form': form, 'form_errors': form_errors})
    else:
        form = VolunteerForm()
        return render(request,'joinus.html',{'form': form})


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
                location_name = form.cleaned_data['location']
                lat, lon = get_lat_lon_from_location(location_name)
                profile.latitude = lat
                profile.longitude = lon
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



def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')  