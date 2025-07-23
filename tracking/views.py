import requests
from datetime import datetime
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.utils.http import urlencode
#Login logic 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required



def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            # Authenticate with username, not email
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('list_packages')  # Change to your success URL
            else:
                messages.error(request, "Invalid email or password.")
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")

    return render(request, 'login.html')

@login_required
def admin_logout_view(request):
    logout(request)
    return redirect('login')


def track_package_view(request):
    return render(request, 'tracking/track_package.html')


def package_results_view(request):
    tracking_number = request.GET.get('tracking_number')
    package = None
    error = None

    if tracking_number:
        try:
            package = Package.objects.prefetch_related('history').get(tracking_number=tracking_number)
        except Package.DoesNotExist:
            error = "Tracking number not found. Please check and try again."
    else:
        error = "Please enter a tracking number."

    if package:
        return render(request, 'tracking/package_details.html', {'package': package})
    
    # show the tracking form again with error message
    return render(request, 'tracking/track_package.html', {
        'error': error,
        'tracking_number': tracking_number
    })

@login_required
def list_packages_view(request):
    packages = Package.objects.all().order_by('-updated_at')
    
    for pkg in packages:
        try:
            base_track_url = request.build_absolute_uri(reverse('package_results'))
            pkg.view_url = f"{base_track_url}?tracking_number={pkg.tracking_number}"
        except Exception as e:
            pkg.view_url = "#"
            print(f"Error generating view_url for {pkg.tracking_number}: {e}")

    context = {
        'packages': packages,
        'page_title': 'All Packages'
    }
    return render(request, 'tracking/list_packages.html', context)


def geocode_city(city, country='Nigeria'):
    """Use Nominatim API to get latitude and longitude from city name with country context."""
    url = 'https://nominatim.openstreetmap.org/search'
    query = f"{city}, {country}" if country else city
    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None

@login_required
def create_package(request):
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number')
        status = request.POST.get('status')
        current_city = request.POST.get('current_city')
        destination_city = request.POST.get('destination_city')
        estimated_delivery_str = request.POST.get('estimated_delivery')

        # Parse estimated delivery datetime
        try:
            estimated_delivery = datetime.strptime(estimated_delivery_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            estimated_delivery = None

        # Parse current city lat/lon
        try:
            lat = float(request.POST.get('latitude')) if request.POST.get('latitude') else None
            lon = float(request.POST.get('longitude')) if request.POST.get('longitude') else None
        except ValueError:
            lat, lon = None, None

        # Parse destination city lat/lon
        try:
            dest_lat = float(request.POST.get('destination_latitude')) if request.POST.get('destination_latitude') else None
            dest_lon = float(request.POST.get('destination_longitude')) if request.POST.get('destination_longitude') else None
        except ValueError:
            dest_lat, dest_lon = None, None

        # Fallback geocode if any missing
        if lat is None or lon is None:
            lat, lon = geocode_city(current_city)
        if dest_lat is None or dest_lon is None:
            dest_lat, dest_lon = geocode_city(destination_city)

        if tracking_number and current_city and destination_city and estimated_delivery and lat and lon and dest_lat and dest_lon:
            package = Package.objects.create(
                tracking_number=tracking_number,
                status=status,
                current_city=current_city,
                latitude=lat,
                longitude=lon,
                destination_city=destination_city,
                destination_latitude=dest_lat,
                destination_longitude=dest_lon,
                estimated_delivery=estimated_delivery
            )
            return redirect('add_delivery_history', package_id=package.id)

        error = "Please fill all required fields correctly."
        return render(request, 'tracking/create_package.html', {'error': error})

    return render(request, 'tracking/create_package.html')

@login_required
def add_delivery_history(request, package_id):
    package = get_object_or_404(Package, id=package_id)

    delivery_status = package.status # Keep initial status for context if POST fails

    if request.method == 'POST':
        city = request.POST.get('city')
        notes = request.POST.get('notes', '')
        new_status = request.POST.get('delivery_status') # Use a different variable name

        lat_str = request.POST.get('latitude')
        lon_str = request.POST.get('longitude')

        # Convert to float, handle potential errors
        try:
            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None
        except ValueError:
            lat, lon = None, None

        if city and lat is not None and lon is not None: # Ensure lat/lon are not None
            # Create delivery history
            DeliveryHistory.objects.create(
                package=package,
                city=city,
                latitude=lat,
                longitude=lon,
                notes=notes
            )

            # --- CRITICAL FIX HERE ---
            # Update package's current location and status
            package.current_city = city
            package.latitude = lat  # Add this line
            package.longitude = lon # Add this line
            
            if new_status: # Use new_status here
                package.status = new_status
            package.save()

            if 'add_more' in request.POST:
                return redirect('add_delivery_history', package_id=package.id)
            else:
                base_url = reverse('package_results')
                query_string = urlencode({'tracking_number': package.tracking_number})
                return redirect(f'{base_url}?{query_string}')
        else:
            # Handle cases where city, lat, or lon might be missing from POST
            error = "Please enter a valid city and provide latitude/longitude from suggestions."
            return render(request, 'tracking/add_delivery_history.html', {
                'package': package,
                'error': error,
                'delivery_status': new_status if new_status else delivery_status, # Use new_status if provided
                'status_choices': DeliveryStatus.choices, # Use Package.DeliveryStatus.choices
            })

    return render(request, 'tracking/add_delivery_history.html', {
        'package': package,
        'delivery_status': delivery_status,
        'status_choices': DeliveryStatus.choices, # Use Package.DeliveryStatus.choices
    })
