from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView

from todo.models import Task

from .services import (
    get_client_ip,
    get_location_from_ip,
    get_coordinates_from_city,
    get_current_weather,
    get_five_day_forecast,
)


def index(request):
    return render(request, 'weathersite/index.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
             
    else:
        form = UserCreationForm()

    for field in form.fields.values():
        field.widget.attrs.update({'class': 'input'})

    return render(request, 'auth/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = "auth/login.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Welcome back, {form.get_user().username}!"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            "Invalid username or password. Please try again."
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(
                request,
                "You have been logged out successfully."
            )
        return super().dispatch(request, *args, **kwargs)


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
    tasks_preview = Task.objects.filter(user=request.user).order_by('-created_at')[:5]

    context = {
        'city_name': location['city'],
        'weather': weather,
        'forecast': forecast,
        'search_error': search_error,
        'searched_city': searched_city,
        'tasks_preview': tasks_preview,
    }
    return render(request, 'weathersite/home.html', context)