from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from .models import Service, Review


def index(request):
    services = Service.objects.filter(is_displayed=True)
    return render(request, 'main/index.html', {'services': services})

def reviews(request):
    reviews = Review.objects.all()
    return render(request, 'main/reviews.html', {'reviews': reviews})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('channels')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/registration.html', {'form': form})







