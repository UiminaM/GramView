from django.urls import path
from . import views
from .forms import CustomLoginView


urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', CustomLoginView.as_view(), name='auth'),
    path('regis/', views.register_view, name='regis'),
    path('reviews/', views.reviews, name='reviews')
]