"""
URL configuration for the assistant app.
"""

from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('context/', views.get_context, name='context'),
]
