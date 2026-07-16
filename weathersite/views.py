from django.shortcuts import render,redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .services import (
    get_client_ip,
    get_location_from_ip,
    get_coordinates_from_city,
    get_current_weather,
    get_five_day_forecast,
)


def index(request):
    return render(request, 'weathersite/index.html')


def home(request):
    searched_city = request.GET.get('city', '').strip()
    location = None
    search_error = None

    if searched_city:
        location = get_coordinates_from_city(searched_city)
        if location is None:
            search_error = f'Could not find "{searched_city}". Showing your detected location instead.'

    if location is None:
        ip = get_client_ip(request)
        location = get_location_from_ip(ip)

    weather = get_current_weather(location['lat'], location['lon'])
    forecast = get_five_day_forecast(location['lat'], location['lon'])

    context = {
        'city_name': location['city'],
        'weather': weather,         
        'forecast': forecast, 
        'search_error': search_error,
        'searched_city': searched_city,  
    }
    return render(request, 'weathersite/home.html', context)


def register(request):
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()     
            login(request, user)  
            return redirect('home')
    else:
        form = UserCreationForm()
 
    return render(request, 'auth/register.html', {'form': form})
 
 
@login_required
def home(request):
    searched_city = request.GET.get('city', '').strip()
    location = None
    search_error = None

    if searched_city:
        location = get_coordinates_from_city(searched_city)
        if location is None:
            search_error = f'Could not find "{searched_city}". Showing your detected location instead.'
 
    if location is None:
        ip = get_client_ip(request)
        location = get_location_from_ip(ip)
 
    weather = get_current_weather(location['lat'], location['lon'])
    forecast = get_five_day_forecast(location['lat'], location['lon'])
 
    context = {
        'city_name': location['city'],
        'weather': weather,
        'forecast': forecast,
        'search_error': search_error,
        'searched_city': searched_city,
    }
    return render(request, 'weathersite/home.html', context)