from django.test import TestCase

# Create your tests here.
"""
Tests for weathersite/services.py

These test the LOGIC in services.py (parsing responses, handling failures)
without making any real network calls. We use unittest.mock.patch to
temporarily replace requests.get with a fake version that returns whatever
JSON we tell it to — this is called "mocking".

Run these with: python manage.py test weathersite
"""

from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from . import services


class GetClientIpTests(SimpleTestCase):
    """Tests for get_client_ip() — no mocking needed, it's pure logic."""

    def test_uses_x_forwarded_for_when_present(self):
        # request.META is just a plain dict in Django, so we can build
        # a fake one by hand — no need for a real HTTP request.
        fake_request = Mock()
        fake_request.META = {
            'HTTP_X_FORWARDED_FOR': '203.0.113.5, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1',
        }

        ip = services.get_client_ip(fake_request)

        # Should take the FIRST ip in the forwarded-for chain, and strip
        # any surrounding whitespace.
        self.assertEqual(ip, '203.0.113.5')

    def test_falls_back_to_remote_addr(self):
        fake_request = Mock()
        fake_request.META = {'REMOTE_ADDR': '198.51.100.7'}

        ip = services.get_client_ip(fake_request)

        self.assertEqual(ip, '198.51.100.7')


class GetLocationFromIpTests(SimpleTestCase):
    """Tests for get_location_from_ip()."""

    def test_local_ip_returns_fallback_immediately(self):
        # No mocking needed here — local IPs should never even reach
        # requests.get(), so we can just call the real function.
        location = services.get_location_from_ip('127.0.0.1')

        self.assertEqual(location, services.DEFAULT_FALLBACK_LOCATION)

    @patch('weathersite.services.requests.get')
    def test_successful_lookup_returns_parsed_location(self, mock_get):
        # mock_get is a fake version of requests.get. We control exactly
        # what it returns when called, instead of hitting the real internet.
        mock_get.return_value.json.return_value = {
            'status': 'success',
            'city': 'Pokhara',
            'lat': 28.2096,
            'lon': 83.9856,
        }
        mock_get.return_value.raise_for_status = Mock()  # pretend no HTTP error

        location = services.get_location_from_ip('8.8.8.8')

        self.assertEqual(location, {'city': 'Pokhara', 'lat': 28.2096, 'lon': 83.9856})

    @patch('weathersite.services.requests.get')
    def test_api_failure_status_returns_fallback(self, mock_get):
        # Simulate ip-api.com responding but saying the lookup failed
        # (e.g. invalid IP, rate limited).
        mock_get.return_value.json.return_value = {'status': 'fail'}
        mock_get.return_value.raise_for_status = Mock()

        location = services.get_location_from_ip('8.8.8.8')

        self.assertEqual(location, services.DEFAULT_FALLBACK_LOCATION)

    @patch('weathersite.services.requests.get')
    def test_network_error_returns_fallback(self, mock_get):
        # Simulate the request failing entirely (no internet, timeout, etc).
        mock_get.side_effect = services.requests.RequestException('boom')

        location = services.get_location_from_ip('8.8.8.8')

        self.assertEqual(location, services.DEFAULT_FALLBACK_LOCATION)


class GetCurrentWeatherTests(SimpleTestCase):
    """Tests for get_current_weather()."""

    def test_returns_none_when_no_api_key_configured(self):
        # Temporarily pretend the API key is empty, without touching the
        # real .env file — this only affects this one test.
        with patch('weathersite.services.OPENWEATHER_API_KEY', ''):
            result = services.get_current_weather(27.7, 85.3)

        self.assertIsNone(result)

    @patch('weathersite.services.OPENWEATHER_API_KEY', 'fake-key-for-testing')
    @patch('weathersite.services.requests.get')
    def test_successful_response_is_parsed_correctly(self, mock_get):
        # A trimmed-down version of what OpenWeather actually returns —
        # only the fields our code reads.
        mock_get.return_value.json.return_value = {
            'main': {'temp': 22.4, 'feels_like': 23.9, 'humidity': 58},
            'weather': [{'description': 'clear sky', 'icon': '01d'}],
            'wind': {'speed': 2.5},  # m/s
        }
        mock_get.return_value.raise_for_status = Mock()

        result = services.get_current_weather(27.7, 85.3)

        self.assertEqual(result['temp'], 22)          # rounded from 22.4
        self.assertEqual(result['feels_like'], 24)     # rounded from 23.9
        self.assertEqual(result['condition'], 'Clear Sky')  # .title()
        self.assertEqual(result['humidity'], 58)
        self.assertEqual(result['emoji'], '☀️')         # '01' maps to sun
        # 2.5 m/s * 3.6 = 9 km/h
        self.assertEqual(result['wind_speed'], 9)

    @patch('weathersite.services.OPENWEATHER_API_KEY', 'fake-key-for-testing')
    @patch('weathersite.services.requests.get')
    def test_network_error_returns_none(self, mock_get):
        mock_get.side_effect = services.requests.RequestException('boom')

        result = services.get_current_weather(27.7, 85.3)

        self.assertIsNone(result)


class GetFiveDayForecastTests(SimpleTestCase):
    """Tests for get_five_day_forecast()."""

    @patch('weathersite.services.OPENWEATHER_API_KEY', 'fake-key-for-testing')
    @patch('weathersite.services.requests.get')
    def test_filters_to_one_entry_per_day(self, mock_get):
        # OpenWeather's real response has readings every 3 hours (8/day).
        # We only build a couple of fake entries here to keep it readable —
        # just enough to prove the "keep only 12:00:00" filter works.
        mock_get.return_value.json.return_value = {
            'list': [
                {
                    'dt_txt': '2026-07-15 09:00:00',
                    'main': {'temp': 20},
                    'weather': [{'description': 'clouds', 'icon': '03d'}],
                },
                {
                    'dt_txt': '2026-07-15 12:00:00',  # this one should be kept
                    'main': {'temp': 24},
                    'weather': [{'description': 'clear sky', 'icon': '01d'}],
                },
                {
                    'dt_txt': '2026-07-15 15:00:00',
                    'main': {'temp': 25},
                    'weather': [{'description': 'clouds', 'icon': '03d'}],
                },
            ]
        }
        mock_get.return_value.raise_for_status = Mock()

        forecast = services.get_five_day_forecast(27.7, 85.3)

        self.assertEqual(len(forecast), 1)
        self.assertEqual(forecast[0]['date'], '2026-07-15')
        self.assertEqual(forecast[0]['temp'], 24)

    @patch('weathersite.services.OPENWEATHER_API_KEY', 'fake-key-for-testing')
    @patch('weathersite.services.requests.get')
    def test_network_error_returns_empty_list(self, mock_get):
        mock_get.side_effect = services.requests.RequestException('boom')

        forecast = services.get_five_day_forecast(27.7, 85.3)

        self.assertEqual(forecast, [])