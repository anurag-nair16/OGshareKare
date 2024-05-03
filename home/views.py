import requests
from django.shortcuts import render, redirect
from .forms import CreateUserForm,DonationForm,VolunteerForm,NGORegistrationForm, NGOProfileForm, ProductForm, CampaignForm, DonorForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import User, Donation, NGO, NGOProfile, Product, CreateCampaign, Donor, Volunteer, Notification
from django.utils import timezone
import math
from itertools import permutations
from django.shortcuts import render
from .forms import MarkAsReadForm

def mark_as_read(request):
    if request.method == 'POST':
        form = MarkAsReadForm(request.POST)
        if form.is_valid():
            notification_id = form.cleaned_data['notification_id']
            notification = Notification.objects.get(pk=notification_id)
            notification.mark_as_read()
    return redirect('view_notify')

def view_notify(request):
    unread_notifications = Notification.objects.filter(user=request.user, read=False)
    read_notifications = Notification.objects.filter(user=request.user, read=True)
    
    notifications = list(unread_notifications) + list(read_notifications)
    return render(request, 'notifications.html',{'notifications':notifications})

#list of volunteers (NGO)
def view_volunteers(request):
    volunteers = Volunteer.objects.all()

    availability = request.GET.get('availability')
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

    lat, lng = get_lat_long(request.user.ngo.ngoprofile.location)
    print(lat,lng)

    return render(request, 'view_volunteers.html', context)


def get_lat_long(location):

    print(location)
    api_key = 'AIzaSyDBr2z__qKnRrmI2V1Cwf4vs8fUzixEOtQ'
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}'

    response = requests.get(url)
    print(response)
    data = response.json()
    print(data)
    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        return None, None
    


def collect_donations(request):
    if request.method == 'POST':
        selected_donation_ids = request.POST.getlist('selected_donations')
        selected_donations = Donation.objects.filter(id__in=selected_donation_ids)
        
        if selected_donations.exists():
            # Get donor locations
            donor_locations = [(donation.user.donor.latitude, donation.user.donor.longitude) 
                               for donation in selected_donations if donation.user.donor.latitude and donation.user.donor.longitude]
            
            # Get NGO location
            ngo_location = (request.user.ngo.latitude, request.user.ngo.longitude)
            print(ngo_location)
            # Solve TSP
            optimal_route, total_distance = solve_tsp(ngo_location, donor_locations)
            
            location_names=[]
            for lat,lon in optimal_route:
                location = Donor.objects.filter(latitude=lat, longitude=lon).first()
                location_names.append(location.location)
            donations = Donation.objects.all()

            route=json.dumps(optimal_route)

            figure = folium.Figure()
            route_coordinates = json.loads(route)
            
            # Add NGO location at the start of the route
            ngo_location = (request.user.ngo.latitude, request.user.ngo.longitude)
            route_coordinates.insert(0, ngo_location)
            
            # Get the route from OSRM
            osrm_route = get_osrm_route(route_coordinates)
            
            m = folium.Map(location=route_coordinates[0], zoom_start=10)
            m.add_to(figure)
            
            # Mark each point of the route on the map
            for point in route_coordinates:
                folium.Marker(location=point, icon=folium.Icon(color='blue')).add_to(m)

            for idx, point in enumerate(route_coordinates):
                if idx == 0:
                    folium.Marker(location=point, icon=folium.Icon(color='green'), popup='Start').add_to(m)
                elif idx == len(route_coordinates) - 1:
                    folium.Marker(location=point, icon=folium.Icon(color='red'), popup='End').add_to(m)
                else:
                    folium.Marker(location=point, icon=folium.DivIcon(html=f'<div style="font-size: 20pt; color: black;">{idx}</div>')).add_to(m)
            
            folium.PolyLine(osrm_route, weight=8, color='blue', opacity=0.6).add_to(m)
            figure.render()

            context = {
                'location_names':location_names,
                'optimal_route': optimal_route,
                'total_distance': total_distance,
                'donations': donations,
                'map': figure, 
                'route': json.dumps(route_coordinates), 
            }
            
            # return redirect('showroute', route=json.dumps(optimal_route), loc=json.dumps(location_names))
            return render(request, 'optimized_route.html', context)
    
    donations = Donation.objects.all()

    context = {
        'donations': donations,
    }

    return render(request, 'collect_donations.html', context)


#provides optimized route for NGO to collect donations
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


#provide lat and long from location name
def get_lat_lon_from_location(location_name):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={location_name}, India"
    response = requests.get(url)
    data = response.json()
    
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    else:
        return None, None

#calculates distance
def haversine_distance(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    r = 6371  # Radius of the earth in kilometers
    return round(r * c, 2)


#index page
def home(request):
    return render(request,'index.html',{})


#view the list of camapigns  (donor)
@login_required(login_url='login')
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

#add listing for the item required  (NGO)
@login_required(login_url='login')
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

#view the list of donations made by the user (NGO)
@login_required(login_url='login')
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


#home page (NGO)
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
    # if query:
    #     donations = DonationDocument.search().query("match", _all=query)
    # else:
    #     donations = Donation.objects.all()

    ngo_latitude = profile.latitude
    ngo_longitude = profile.longitude
    print(ngo_latitude)
    print(ngo_longitude)

    if ngo_latitude and ngo_longitude:
        donation = sorted(donation,key=lambda x: haversine_distance(ngo_latitude, ngo_longitude, x.user.donor.latitude, x.user.donor.longitude))
    
    selected_donation_ids = request.session.get('selected_donations', [])

    context = {
        'ngoname': profile.ngoname,
        'regno': profile.regno,
        'donation': donation,
        'selected_donations': selected_donation_ids,
    }

    return render(request,'ngo_dashboard.html',context)


#view the list of donations asked by the NGO (donor)
@login_required(login_url='login')
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

#home page (donor)
@login_required(login_url='login')
def main_home(request):
    query = request.GET.get('q')
    products = Product.objects.filter(productName__icontains=query) if query else Product.objects.all()

    nearest_campaigns = []

    if request.user.is_authenticated:
        if not request.session.get('modal_shown', False):
            request.session['modal_shown'] = True
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
                        if not product.ngo.latitude and not product.ngo.longitude:
                            ngo_lat, ngo_lon = get_lat_lon_from_location(ngo_location)
                        else:
                            ngo_lat=product.ngo.latitude
                            ngo_lon=product.ngo.longitude
                        if ngo_lat and ngo_lon:
                            try:
                                product.ngo.latitude = ngo_lat
                                product.ngo.longitude = ngo_lon
                                product.ngo.save()
                            except Exception as e:
                                print(f"Error calculating distance: {e}")

                    products = sorted(products, key=lambda x: haversine_distance(user_lat, user_lon, x.ngo.latitude, x.ngo.longitude))
                    unread_notifications = Notification.objects.filter(user=request.user, read=False)
                    has_new_notifications = unread_notifications.exists()
                    print(has_new_notifications)
                    context = {'products': products, 'nearest_campaigns': nearest_campaigns, 'has_new_notifications': has_new_notifications}
                    return render(request, 'home.html', context)
                
            except Donor.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error fetching user location: {e}")

    has_new_notifications = False
    context = {'products': products, 'nearest_campaigns': nearest_campaigns, 'has_new_notifications': has_new_notifications}
    return render(request, 'home.html', context)

#register with us (Both)
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
    
#Volunteer form 
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

#create donation item (donor)
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


#register as an ngo
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

#login as ngo or donor
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

#ngo profile detail (NGO)
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
    
#ngo profile (NGO)
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

#donor profile (donor)
@login_required
def user_profile(request):
    return render(request, 'userprofile.html')

#creates a campaign (NGO)
@login_required
def create_campaign(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.ngo = request.user
            campaign.save()
            messages.success(request, 'Campaign listed succesfully')
            Notification.send_campaign_notifications(campaign.ngo)
            return redirect('ngo_dashboard')
    else:
        form = CampaignForm()
    
    return render(request, 'create_campaign.html', {'form': form})

#logout
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')  


























import requests
import json
import polyline
import folium


def get_route(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat):
    loc = "{},{};{},{}".format(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat)
    url = "http://router.project-osrm.org/route/v1/driving/"
    r = requests.get(url + loc) 
    if r.status_code!= 200:
        return {}
    res = r.json()   
    routes = polyline.decode(res['routes'][0]['geometry'])
    start_point = [res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0]]
    end_point = [res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0]]
    distance = res['routes'][0]['distance']
    
    out = {'route':routes,
           'start_point':start_point,
           'end_point':end_point,
           'distance':distance
          }

    return out


def showmap(request):
    return render(request,'showmap.html')

# def showroute(request, route ,loc):
#     figure = folium.Figure()
#     route_coordinates = json.loads(route)
    
#     # Add NGO location at the start of the route
#     ngo_location = (request.user.ngo.latitude, request.user.ngo.longitude)
#     route_coordinates.insert(0, ngo_location)
    
#     # Get the route from OSRM
#     osrm_route = get_osrm_route(route_coordinates)
    
#     m = folium.Map(location=route_coordinates[0], zoom_start=10)
#     m.add_to(figure)
    
#     # Mark each point of the route on the map
#     for point in route_coordinates:
#         folium.Marker(location=point, icon=folium.Icon(color='blue')).add_to(m)

#     for idx, point in enumerate(route_coordinates):
#         if idx == 0:
#             folium.Marker(location=point, icon=folium.Icon(color='green'), popup='Start').add_to(m)
#         elif idx == len(route_coordinates) - 1:
#             folium.Marker(location=point, icon=folium.Icon(color='red'), popup='End').add_to(m)
#         else:
#             folium.Marker(location=point, icon=folium.DivIcon(html=f'<div style="font-size: 20pt; color: black;">{idx}</div>')).add_to(m)
    
#     folium.PolyLine(osrm_route, weight=8, color='blue', opacity=0.6).add_to(m)
#     figure.render()

#     print(loc)
#     loc = loc.split('\n')

#     print(loc)
    
#     context = {
#         'map': figure, 
#         'route': json.dumps(route_coordinates), 
#         'loc':loc,
#         }
#     return render(request, 'showroute.html', context)

def get_osrm_route(coordinates):
    loc = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    url = f"http://router.project-osrm.org/route/v1/driving/{loc}"
    r = requests.get(url)
    
    if r.status_code != 200:
        return []
    
    res = r.json()
    osrm_route = polyline.decode(res['routes'][0]['geometry'])
    
    return osrm_route