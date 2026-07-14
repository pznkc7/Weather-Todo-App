

import requests
from decouple import config

OPENWEATHER_API_KEY = config('OPENWEATHER_API_KEY', default='')

IP_GEOLOCATION_URL = 'http://ip-api.com/json/{ip}'

DEFAULT_FALLBACK_LOCATION = {
    'city': 'Kathmandu',
    'lat': 27.7172,
    'lon': 85.3240,
}

def get_client_ip(request):

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def _is_local_ip(ip):
    return ip in ('127.0.0.1', 'localhost', '::1') or ip.startswith('192.168.') or ip.startswith('10.')

def get_location_from_ip(ip):
    if not ip or _is_local_ip(ip):
        return DEFAULT_FALLBACK_LOCATION

    try:
        response = requests.get(IP_GEOLOCATION_URL.format(ip=ip), timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'success':
            return DEFAULT_FALLBACK_LOCATION

        return {
            'city': data.get('city', 'Unknown'),
            'lat': data['lat'],
            'lon': data['lon'],
        }
    except (requests.RequestException, KeyError, ValueError):
        return DEFAULT_FALLBACK_LOCATION


_ICON_EMOJI = {
    '01': '☀️',  # clear
    '02': '⛅',  # few clouds
    '03': '☁️',  # scattered clouds
    '04': '☁️',  # broken/overcast clouds
    '09': '🌧️',  # shower rain
    '10': '🌦️',  # rain
    '11': '⛈️',  # thunderstorm
    '13': '❄️',  # snow
    '50': '🌫️',  # mist
}


def _emoji_for(icon_code):
    return _ICON_EMOJI.get(icon_code[:2], '🌡️')


def get_current_weather(lat, lon):
    if not OPENWEATHER_API_KEY:
        return None
    try:
        response = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={
                'lat': lat,
                'lon': lon,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        icon_code = data['weather'][0]['icon']
        return {
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'condition': data['weather'][0]['description'].title(),
            'icon_code': icon_code,
            'emoji': _emoji_for(icon_code),
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed'] * 3.6),  # m/s -> km/h
        }
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def get_five_day_forecast(lat, lon):
    if not OPENWEATHER_API_KEY:
        return []

    try:
        response = requests.get(
            'https://api.openweathermap.org/data/2.5/forecast',
            params={
                'lat': lat,
                'lon': lon,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        daily = [
            entry for entry in data.get('list', [])
            if entry['dt_txt'].endswith('12:00:00')
        ]

        return [
            {
                'date': entry['dt_txt'].split(' ')[0],
                'temp': round(entry['main']['temp']),
                'icon_code': entry['weather'][0]['icon'],
                'emoji': _emoji_for(entry['weather'][0]['icon']),
                'condition': entry['weather'][0]['description'].title(),
            }
            for entry in daily[:5]
        ]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return []