from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'todo'
urlpatterns = [
    path('list/', views.task_list, name='list'),
    path('add/', views.task_create, name='create'),
    path('<int:task_id>/toggle/', views.task_toggle_complete, name='toggle'),
    path('<int:task_id>/delete/', views.task_delete, name='delete'),
]