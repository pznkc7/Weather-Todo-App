"""
Pure-Python location + weather lookups.
No JavaScript/browser geolocation involved: we resolve the visitor's
approximate location from their IP address, then fetch weather for those
coordinates. Good enough for city-level accuracy; not exact GPS.
"""

import requests
from decouple import config

OPENWEATHER_API_KEY = config('OPENWEATHER_API_KEY', default='')

# IP-API's free tier: no key required, ~45 requests/minute.
IP_GEOLOCATION_URL = 'http://ip-api.com/json/{ip}'
DEFAULT_FALLBACK_LOCATION = {
    'city': 'Kathmandu',
    'lat': 27.7172,
    'lon': 85.3240,
}


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip() # separates the client's IP from the rest of the chain
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


# Maps OpenWeather's icon code prefix to a simple emoji
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


def get_coordinates_from_city(city_name):
    """
    Turn a city name typed by the user (e.g. "Pokhara") into {'city', 'lat', 'lon'}.

    Uses OpenWeather's free Geocoding API — same API key you already have,
    no extra signup needed. Returns None if the city can't be found or the
    request fails, so the view can fall back to IP-based location instead.
    """
    if not OPENWEATHER_API_KEY or not city_name:
        return None

    try:
        response = requests.get(
            'https://api.openweathermap.org/geo/1.0/direct',
            params={
                'q': city_name,
                'limit': 1,           # only want the single best match
                'appid': OPENWEATHER_API_KEY,
            },
            timeout=5,
        )
        response.raise_for_status()
        results = response.json()

        if not results:
            return None

        match = results[0]
        return {
            'city': match.get('name', city_name),
            'lat': match['lat'],
            'lon': match['lon'],
        }
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def get_current_weather(lat, lon):
    """
    Fetch current weather for given coordinates from OpenWeather.

    Returns a plain dict the template can use directly, or None if the
    API call fails (missing key, network error, bad response) so the view
    can decide how to degrade gracefully.
    """
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
    """
    Fetch a simplified 5-day forecast (one entry per day, midday reading)
    from OpenWeather's free /forecast endpoint (3-hour steps, 5 days).
    """
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

        # The API returns 3-hour steps; keep the ~midday (12:00) entry per day.
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