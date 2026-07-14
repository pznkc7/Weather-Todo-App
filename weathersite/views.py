from django.shortcuts import render

from .services import get_client_ip, get_location_from_ip, get_current_weather, get_five_day_forecast


def index(request):
    return render(request, 'weathersite/index.html')


def home(request):
    ip = get_client_ip(request)
    location = get_location_from_ip(ip)

    weather = get_current_weather(location['lat'], location['lon'])
    forecast = get_five_day_forecast(location['lat'], location['lon'])

    context = {
        'city_name': location['city'],
        'weather': weather,     
        'forecast': forecast,   
    }
    return render(request, 'weathersite/home.html', context)