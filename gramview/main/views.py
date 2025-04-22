from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm


def index(request):
    return render(request, 'main/index.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('auth')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/registration.html', {'form': form})

def reviews(request):
    reviews = [
        {
            'avatar': '',
            'username': 'katya23',
            'date': '2025-04-20',
            'text': 'Очень классный сервис, мне всё понравилось!',
            'rating': 5
        },
        {
            'avatar': '',
            'username': 'maksym_88',
            'date': '2025-04-18',
            'text': 'Хорошо, но есть куда расти.',
            'rating': 3
        },
        {
            'avatar': '',
            'username': 'lena_k',
            'date': '2025-04-17',
            'text': 'Не совсем то, что я ожидала, но сойдёт.',
            'rating': 2
        }
    ]
    return render(request, 'main/reviews.html', {'reviews': reviews})





