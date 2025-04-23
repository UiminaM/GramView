from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from main.models import CustomUser, Review
from .forms import ReviewForm
from .forms import ProfileEditForm
from django.contrib import messages


def some_view(request):
    is_advanced = request.user.groups.filter(name='advanced').exists()
    return is_advanced


def channels_view(request):
    return render(request, 'channels/channels.html', {'is_advanced': some_view(request)})


def posts_view(request):
    return render(request, 'posts/post_form.html', {'is_advanced': some_view(request)})


@login_required
@user_passes_test(lambda u: u.groups.filter(name='advanced').exists())
def my_channels_view(request):
    return render(request, 'channels/channels.html', {'is_advanced': some_view(request)})


@login_required
def profile_view(request):
    user = request.user
    profile_picture = user.profile_picture
    reviews = Review.objects.filter(id_profile=user)

    if reviews.exists():
        review = reviews.first()
        form = ReviewForm(instance=review)
    else:
        form = ReviewForm()

    if request.method == 'POST':
        if 'submit_review' in request.POST:
            if reviews.exists():
                review = reviews.first()
                form = ReviewForm(request.POST, instance=review)
            else:
                form = ReviewForm(request.POST)

            if form.is_valid():
                form.instance.id_profile = user
                form.save()
                messages.success(request, 'Ваш отзыв успешно добавлен!')
                return redirect('profile')

        elif 'delete_review' in request.POST:
            if reviews.exists():
                review = reviews.first()
                review.delete()
                messages.success(request, 'Отзыв успешно удален!')
            return redirect('profile')

    return render(request, 'profile/profile.html', {'user': user, 'form': form, 'profile_picture': profile_picture})


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=user)

    return render(request, 'profile/edit_profile.html', {'form': form})