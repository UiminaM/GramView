import plotly.graph_objs as go
from django.db.models import Count, Avg, Sum
from collections import Counter
from datetime import datetime, timedelta
from account.models import Post, Comment, SubscriberGrowth

def generate_dynamic_activity_chart(channel, detailed=False):
    today = datetime.now()
    three_months_ago = today - timedelta(weeks=12)

    posts = Post.objects.filter(
        channel=channel,
        published_at__gte=three_months_ago
    )
    data_by_week = {}

    for post in posts:
        post_date = post.published_at
        days_ahead = 6 - post_date.weekday()
        sunday_date = post_date + timedelta(days=days_ahead)
        sunday_date = sunday_date.date()

        if sunday_date not in data_by_week:
            data_by_week[sunday_date] = {
                'views_sum': 0,
                'posts_count': 0,
                'reactions_sum': 0,
                'forwards_sum': 0,
            }

        data_by_week[sunday_date]['views_sum'] += post.reactions_count
        data_by_week[sunday_date]['posts_count'] += 1

        if detailed:
            if hasattr(post, 'reactions_count'):
                data_by_week[sunday_date]['reactions_sum'] += post.reactions_count
            if hasattr(post, 'forwards_count'):
                data_by_week[sunday_date]['forwards_sum'] += post.forwards_count

    sorted_dates = sorted(data_by_week.keys())

    dates = []
    avg_views = []
    posts_counts = []
    reactions_sums = []
    forwards_sums = []

    for date in sorted_dates:
        stats = data_by_week[date]
        dates.append(date.strftime('%d.%m.%Y'))
        avg_views.append(stats['views_sum'] / stats['posts_count'] if stats['posts_count'] else 0)
        posts_counts.append(stats['posts_count'])
        if detailed:
            reactions_sums.append(stats['reactions_sum'])
            forwards_sums.append(stats['forwards_sum'])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=avg_views,
        mode='lines+markers',
        name='Среднее количество реакций'
    ))

    fig.add_trace(go.Scatter(
        x=dates,
        y=posts_counts,
        mode='lines+markers',
        name='Количество постов'
    ))

    if detailed:
        fig.add_trace(go.Scatter(
            x=dates,
            y=reactions_sums,
            mode='lines+markers',
            name='Сумма реакций за неделю'
        ))
        fig.add_trace(go.Scatter(
            x=dates,
            y=forwards_sums,
            mode='lines+markers',
            name='Сумма пересылок за неделю'
        ))

    fig.update_layout(
        title='Детальная динамика активности' if detailed else 'Динамика активности',
        xaxis_title='Дата (воскресенье недели)',
        yaxis_title='Значение',
        template='plotly_white',
        hovermode='x unified'
    )

    return fig.to_html(full_html=False)



def generate_comments_classification_chart(channel):
    classification_counts = (
        Comment.objects.filter(post__channel=channel)
        .values('classification')
        .annotate(count=Count('id'))
    )

    labels = []
    values = []

    for entry in classification_counts:
        labels.append(dict(Comment.CLASS_CHOICES).get(entry['classification'], entry['classification']))
        values.append(entry['count'])

    if not labels:
        labels = ['Нет данных']
        values = [1]

    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, hole=0.4)
    ])

    fig.update_layout(
        title='Распределение классов комментариев',
        annotations=[dict(text='Классы', x=0.5, y=0.5, font_size=18, showarrow=False)]
    )

    return fig.to_html(full_html=False)

def generate_peak_activity_time_chart(channel, detailed=False):
    today = datetime.now()
    three_months_ago = today - timedelta(weeks=12)

    comments = Comment.objects.filter(
        post__channel=channel,
        published_at__gte=three_months_ago
    )

    posts = Post.objects.filter(
        channel=channel,
        published_at__gte=three_months_ago
    )

    hours = list(range(24))
    hours_count_comments = {hour: 0 for hour in hours}
    hours_count_reactions = {hour: 0 for hour in hours}
    hours_count_forwards = {hour: 0 for hour in hours}

    for comment in comments:
        hour = comment.published_at.hour
        hours_count_comments[hour] += 1

    if detailed:
        for post in posts:
            hour = post.published_at.hour
            hours_count_reactions[hour] += post.reactions_count
            forwards = getattr(post, 'forwards_count', 0)
            hours_count_forwards[hour] += forwards

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=hours,
        y=[hours_count_comments[h] for h in hours],
        name="Комментарии",
        marker_color='mediumseagreen'
    ))

    if detailed:
        fig.add_trace(go.Bar(
            x=hours,
            y=[hours_count_reactions[h] for h in hours],
            name="Реакции",
            marker_color='royalblue'
        ))

        fig.add_trace(go.Bar(
            x=hours,
            y=[hours_count_forwards[h] for h in hours],
            name="Пересылки",
            marker_color='firebrick'
        ))

    fig.update_layout(
        title='Время максимальной активности (по часам)',
        xaxis_title='Час дня',
        yaxis_title='Количество',
        barmode='group',
        template='plotly_white',
        height=500,
    )

    return fig.to_html(full_html=False)


def generate_subscriber_growth_chart(channel):
    growth_data = SubscriberGrowth.objects.filter(channel=channel).order_by('date')
    dates = [item.date.strftime('%d.%m.%Y') for item in growth_data]
    subscribers = [item.subscribers_count for item in growth_data]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=subscribers,
        mode='lines+markers',
        name='Подписчики',
        line=dict(color='royalblue')
    ))

    fig.update_layout(
        title='Рост подписчиков по неделям',
        xaxis_title='Неделя (воскресенье)',
        yaxis_title='Количество подписчиков',
        template='plotly_white'
    )

    return fig.to_html(full_html=False)


def generate_most_discussed_posts_chart(channel):
    top_posts = Post.objects.filter(channel=channel).order_by('-comments_count')[:10]

    post_titles = [post.text[:30] + '...' if len(post.text) > 30 else post.text for post in top_posts]
    comments_counts = [post.comments_count for post in top_posts]
    reactions_counts = [post.reactions_count for post in top_posts]
    forwards_counts = [post.forwards_count if hasattr(post, 'forwards_count') else 0 for post in top_posts]  # вдруг нет поля

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=post_titles,
        x=comments_counts,
        name='Комментарии',
        orientation='h',
        marker_color='mediumseagreen'
    ))

    fig.add_trace(go.Bar(
        y=post_titles,
        x=reactions_counts,
        name='Реакции',
        orientation='h',
        marker_color='lightskyblue'
    ))

    fig.add_trace(go.Bar(
        y=post_titles,
        x=forwards_counts,
        name='Пересылки',
        orientation='h',
        marker_color='salmon'
    ))

    fig.update_layout(
        barmode='group',
        title='Топ-10 самых обсуждаемых постов (с реакциями и пересылками)',
        xaxis_title='Количество',
        yaxis_title='Посты',
        template='plotly_white',
        yaxis=dict(autorange="reversed")
    )

    return fig.to_html(full_html=False)


def generate_top_commentators_chart(channel):
    today = datetime.now()
    three_months_ago = today - timedelta(weeks=12)

    comments = Comment.objects.filter(
        post__channel=channel,
        published_at__gte=three_months_ago
    )

    usernames = [comment.author_name for comment in comments if comment.author_name]

    counter = Counter(usernames)
    top_users = counter.most_common(10)

    if not top_users:
        return "<div>Нет данных для отображения</div>"

    usernames = [user for user, _ in top_users]
    counts = [count for _, count in top_users]

    fig = go.Figure([
        go.Bar(
            x=counts,
            y=usernames,
            orientation='h',
            marker_color='mediumslateblue'
        )
    ])

    fig.update_layout(
        title='Самые активные комментаторы',
        xaxis_title='Количество комментариев',
        yaxis_title='Пользователи',
        template='plotly_white',
        yaxis=dict(autorange="reversed")
    )

    return fig.to_html(full_html=False)
