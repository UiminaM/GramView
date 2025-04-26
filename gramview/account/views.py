from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from asgiref.sync import async_to_sync
from main.models import CustomUser, Review
from .models import Channels, UserChannelAccess
from .forms import ReviewForm
from .forms import ProfileEditForm
from .forms import BaseChannelForm, AdvanceChannelForm
from .telegram_auth import authenticate_user
from .telegram_utils import get_telegram_client, check_channel, get_channel_data


def is_advanced_user(user):
    return user.groups.filter(name='advanced').exists()


def channels_view(request):
    return render(request, 'channels/channels.html', {'is_advanced': is_advanced_user(request)})

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


def channels(request):
    query = request.GET.get('q', '')
    only_my = request.GET.get('my', '') == 'on'
    channels = Channels.objects.filter(users=request.user)

    if query:
        channels = channels.filter(name__icontains=query)

    if only_my:
        channels = channels.filter(userchannelaccess__user=request.user, userchannelaccess__is_owner=True)

    return render(request, 'channels/channels.html', {
        'channels': channels,
        'query': query,
        'only_my': only_my,
    })

def process_form(request, is_advanced):
    if is_advanced:
        form = AdvanceChannelForm(request.POST)
    else:
        form = BaseChannelForm(request.POST)

    if form.is_valid():
        username = form.cleaned_data.get('username')
        existing_channel = Channels.objects.filter(username=username).first()

        if existing_channel:
            access, created = UserChannelAccess.objects.get_or_create(
                channel=existing_channel,
                user=request.user,
                defaults={'is_owner': is_advanced}
            )
            if not created and access.is_owner != is_advanced:
                access.is_owner = is_advanced
                access.save()
            return redirect('channels')

        if is_advanced:
            phone = form.cleaned_data['phone_number']
            code = form.cleaned_data['verification_code']
            try:
                client, session_str = authenticate_user(phone, code)
            except Exception as e:
                messages.error(request, f"Ошибка авторизации: {str(e)}")
                return None
            result = async_to_sync(check_channel)(username, client)

        else:
            client = async_to_sync(get_telegram_client)()
            result = async_to_sync(check_channel)(username, client)

        if result:
            channel_data = async_to_sync(get_channel_data)(username, client, session_str)
            if channel_data:
                channel = form.save(commit=False)
                channel.name = channel_data['name']
                channel.username = channel_data['username']
                channel.photo_url = channel_data['photo_url'] or None
                channel.save()

                UserChannelAccess.objects.create(
                    channel=channel,
                    user=request.user,
                    is_owner=is_advanced
                )
                return redirect('channels')

        messages.error(request, 'Канал не существует или не найден в Telegram!')

    return None

@login_required
def add_channel(request):
    is_advance = is_advanced_user(request.user)
    base_form = None
    advanced_form = None

    if request.method == 'POST':
        if 'advanced_form' in request.POST:
            response = process_form(request, True)
        else:
            response = process_form(request, False)

        if response:
            return response

    else:
        base_form = BaseChannelForm()
        advanced_form = AdvanceChannelForm()

    return render(request, 'channels/add_channel.html', {
        'base_form': base_form,
        'advanced_form': advanced_form,
        'is_advance': is_advance
    })


@csrf_exempt
def delete_channel(request, channel_id):
    access = UserChannelAccess.objects.get(channel_id=channel_id, user=request.user)
    channel = access.channel
    if request.method == 'POST':
        channel.delete()
    return redirect('channels')






