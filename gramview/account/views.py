from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from main.models import Review
from .models import Channels, UserChannelAccess
from .forms import ReviewForm
from .forms import ProfileEditForm
from .forms import BaseChannelForm, AdvanceChannelForm
from .utils.telegram import check_channel, get_channel_data, start_telegram_auth, authenticate_user
from .utils.graph import generate_dynamic_activity_chart, generate_comments_classification_chart, generate_peak_activity_time_chart, generate_subscriber_growth_chart, generate_most_discussed_posts_chart, generate_top_commentators_chart
import json
import ollama


def is_advanced_user(user):
    return user.groups.filter(name='advanced').exists()


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
    is_advanced = is_advanced_user(request.user)

    access_qs = UserChannelAccess.objects.filter(user=request.user)
    if only_my and is_advanced:
        access_qs = access_qs.filter(is_owner=True)

    channel_ids = access_qs.values_list('channel_id', flat=True)

    channels = Channels.objects.filter(id__in=channel_ids)
    if query:
        channels = channels.filter(name__icontains=query)

    return render(request, 'channels/channels.html', {
        'channels': channels,
        'query': query,
        'only_my': only_my,
        'is_advanced': is_advanced,
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

        channel_data = None

        if is_advanced:
            phone = form.cleaned_data['phone_number']
            code = form.cleaned_data['verification_code']
            try:
                session_str = async_to_sync(authenticate_user)(phone, code)
                result = async_to_sync(check_channel)(username, session_str)
                if result:
                    channel_data = async_to_sync(get_channel_data)(username, session_str, is_advanced)
                else:
                    messages.error(request, 'Канал не найден')
                    return None
            except Exception as e:
                messages.error(request, f"Ошибка авторизации: {str(e)}")
                return None

        else:
            try:
                result = async_to_sync(check_channel)(username, settings.BASE_SESSION)
                if result:
                    channel_data = async_to_sync(get_channel_data)(username, settings.BASE_SESSION, is_advanced)
            except Exception as e:
                messages.error(request, f"Ошибка при проверке канала: {str(e)}")
                return None
        print(channel_data)
        if channel_data:
            channel = Channels.objects.filter(username=username).first()

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
    base_form = BaseChannelForm()
    advanced_form = AdvanceChannelForm()

    phone_number = request.session.get('phone_number', '')

    if request.method == 'POST':
        if 'send_code' in request.POST:
            phone = request.POST.get('phone_number')
            try:
                async_to_sync(start_telegram_auth)(phone)
                request.session['phone_number'] = phone
                messages.success(request, f'Код отправлен на номер {phone}')
            except Exception as e:
                messages.error(request, f'Ошибка при отправке кода: {e}')

        elif 'advanced_form' in request.POST:
            response = process_form(request, True)
            if response:
                request.session.pop('phone_number', None)
                return response

        elif 'base_form' in request.POST:
            response = process_form(request, False)
            if response:
                return response

    return render(request, 'channels/add_channel.html', {
        'base_form': base_form,
        'advanced_form': advanced_form,
        'is_advance': is_advance,
        'phone_number': phone_number,
    })


@csrf_exempt
def delete_channel(request, channel_id):
    access = UserChannelAccess.objects.get(channel_id=channel_id, user=request.user)
    channel = access.channel
    if request.method == 'POST':
        channel.delete()
    return redirect('channels')


@login_required
def channel_detail(request, channel_id):
    channel = Channels.objects.get(id=channel_id)
    user_access = UserChannelAccess.objects.filter(user=request.user, channel=channel).first()

    is_advanced = 'advanced' if user_access.is_owner else 'base'

    graphs_by_role = {
        'base': [
            'Динамика активности',
            'Распределение классов комментариев',
            'Время максимальной активности',
        ],
        'advanced': [
            'Детальная динамика активности',
            'Распределение классов комментариев',
            'Время максимальной активности',
            'Рост подписчиков',
            'Самые обсуждаемые посты',
            'Самые активные комментаторы',
        ]
    }

    available_graphs = graphs_by_role[is_advanced]

    dynamic_activity_graph = generate_dynamic_activity_chart(channel, detailed=False)
    detailed_dynamic_activity_graph = generate_dynamic_activity_chart(channel, detailed=True)
    comments_classification_chart = generate_comments_classification_chart(channel)
    peak_activity_time_chart = generate_peak_activity_time_chart(channel, detailed=(is_advanced == 'advanced'))
    subscriber_growth_chart = generate_subscriber_growth_chart(channel)
    most_discussed_posts_chart = generate_most_discussed_posts_chart(channel)
    top_commentators_chart = generate_top_commentators_chart(channel)

    return render(request, 'channels/channel.html', {
        'channel': channel,
        'available_graphs': available_graphs,
        'dynamic_activity_graph': dynamic_activity_graph,
        'detailed_dynamic_activity_graph': detailed_dynamic_activity_graph,
        'comments_classification_chart': comments_classification_chart,
        'peak_activity_time_chart': peak_activity_time_chart,
        'subscriber_growth_chart': subscriber_growth_chart,
        'most_discussed_posts_chart': most_discussed_posts_chart,
        'top_commentators_chart': top_commentators_chart,
        'is_advanced': is_advanced,
    })


@csrf_exempt
@login_required
def ask_llm(request):
    if request.method == "POST":
        data = json.loads(request.body)
        graph_title = data.get('graph_title')
        question = data.get('question')
        graph_data = data.get('graph_data')
        if not graph_title or not question:
            return JsonResponse({'answer': 'Некорректный запрос.'})

        prompt = f"""Ты — эксперт по аналитике Telegram-каналов.
    Пользователь анализирует график "{graph_title}". Вот данные графика: {graph_data}.
    Вопрос пользователя: "{question}".
    Дай совет по развитию канала, основываясь на цифрах и характере графика.
    """
        try:
            response = ollama.chat(model='mistral', messages=[
                {'role': 'user', 'content': prompt}
            ])
            answer = response['message']['content']
        except Exception as e:
            answer = f"Ошибка при обращении к модели: {str(e)}"

        return JsonResponse({'answer': answer})

    else:
        return JsonResponse({'answer': 'Только POST-запросы разрешены.'})
