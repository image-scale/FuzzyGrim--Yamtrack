"""Statistics functionality for media tracking."""

import calendar
from collections import defaultdict
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.db import models
from django.db.models import Prefetch, Q
from django.utils import timezone

from app.models import TV, Episode, MediaTypes, Season, Status


def get_user_media(user, start_date=None, end_date=None):
    """Get all media items and their counts for a user within date range.

    Args:
        user: The user to get media for
        start_date: Start of date range (None for all time)
        end_date: End of date range (None for all time)

    Returns:
        Tuple of (user_media dict, media_count dict)
    """
    media_models = [
        apps.get_model(app_label='app', model_name=media_type)
        for media_type in user.get_active_media_types()
    ]
    user_media = {}
    media_count = {'total': 0}

    base_episodes = None
    if TV in media_models or Season in media_models:
        if start_date is None and end_date is None:
            base_episodes = Episode.objects.filter(
                related_season__user=user,
            )
        else:
            base_episodes = Episode.objects.filter(
                related_season__user=user,
                end_date__range=(start_date, end_date),
            )

    for model in media_models:
        media_type = model.__name__.lower()
        queryset = None

        if model == TV:
            tv_ids = base_episodes.values_list(
                'related_season__related_tv',
                flat=True,
            ).distinct()
            queryset = TV.objects.filter(id__in=tv_ids).prefetch_related(
                Prefetch(
                    'seasons',
                    queryset=Season.objects.select_related(
                        'item',
                    ).prefetch_related(
                        Prefetch(
                            'episodes',
                            queryset=base_episodes.filter(
                                related_season__related_tv__in=tv_ids,
                            ),
                        ),
                    ),
                ),
            )
        elif model == Season:
            season_ids = base_episodes.values_list(
                'related_season',
                flat=True,
            ).distinct()
            queryset = Season.objects.filter(
                id__in=season_ids,
            ).prefetch_related(
                Prefetch('episodes', queryset=base_episodes),
            )
        elif start_date is None and end_date is None:
            queryset = model.objects.filter(user=user)
        else:
            queryset = model.objects.filter(user=user).filter(
                (
                    Q(start_date__isnull=False)
                    & Q(end_date__isnull=False)
                    & ~(Q(end_date__lt=start_date) | Q(start_date__gt=end_date))
                )
                | (
                    Q(start_date__isnull=False)
                    & Q(end_date__isnull=True)
                    & Q(start_date__gte=start_date)
                    & Q(start_date__lte=end_date)
                )
                | (
                    Q(start_date__isnull=True)
                    & Q(end_date__isnull=False)
                    & Q(end_date__gte=start_date)
                    & Q(end_date__lte=end_date)
                ),
            )

        queryset = queryset.select_related('item')
        user_media[media_type] = queryset
        count = queryset.count()
        media_count[media_type] = count
        media_count['total'] += count

    return user_media, media_count


def get_media_type_distribution(media_count):
    """Get data formatted for Chart.js pie chart.

    Args:
        media_count: Dict of media type to count

    Returns:
        Dict with labels and datasets for Chart.js
    """
    chart_data = {
        'labels': [],
        'datasets': [
            {
                'data': [],
                'backgroundColor': [],
            },
        ],
    }

    colors = {
        'movie': '#FF6384',
        'tv': '#36A2EB',
        'season': '#36A2EB',
        'anime': '#FFCE56',
        'manga': '#4BC0C0',
        'game': '#9966FF',
        'book': '#FF9F40',
        'comic': '#C9CBCF',
        'boardgame': '#7CB342',
    }

    for media_type, count in media_count.items():
        if media_type != 'total' and count > 0:
            label = media_type.replace('_', ' ').title()
            chart_data['labels'].append(label)
            chart_data['datasets'][0]['data'].append(count)
            chart_data['datasets'][0]['backgroundColor'].append(
                colors.get(media_type, '#999999'),
            )
    return chart_data


def get_status_distribution(user_media):
    """Get status distribution for each media type.

    Args:
        user_media: Dict of media type to queryset

    Returns:
        Dict with labels, datasets, and total_completed
    """
    distribution = {}
    total_completed = 0
    status_order = list(Status.values)

    status_colors = {
        Status.COMPLETED.value: '#4CAF50',
        Status.IN_PROGRESS.value: '#2196F3',
        Status.PLANNING.value: '#9E9E9E',
        Status.PAUSED.value: '#FF9800',
        Status.DROPPED.value: '#F44336',
    }

    for media_type, media_list in user_media.items():
        status_counts = dict.fromkeys(status_order, 0)
        counts = media_list.values('status').annotate(count=models.Count('id'))
        for count_data in counts:
            status_counts[count_data['status']] = count_data['count']
            if count_data['status'] == Status.COMPLETED.value:
                total_completed += count_data['count']

        distribution[media_type] = status_counts

    return {
        'labels': [x.replace('_', ' ').title() for x in distribution],
        'datasets': [
            {
                'label': status,
                'data': [
                    distribution[media_type][status] for media_type in distribution
                ],
                'background_color': status_colors.get(status, '#999999'),
                'total': sum(
                    distribution[media_type][status] for media_type in distribution
                ),
            }
            for status in status_order
        ],
        'total_completed': total_completed,
    }


def get_score_distribution(user_media):
    """Get score distribution for each media type.

    Args:
        user_media: Dict of media type to queryset

    Returns:
        Dict with labels, datasets, average_score, and total_scored
    """
    distribution = {}
    total_scored = 0
    total_score_sum = 0
    score_range = range(11)

    for media_type, media_list in user_media.items():
        score_counts = dict.fromkeys(score_range, 0)
        scored_media = media_list.exclude(score__isnull=True)

        for media in scored_media:
            binned_score = int(media.score)
            score_counts[binned_score] += 1
            total_scored += 1
            total_score_sum += float(media.score)

        distribution[media_type] = score_counts

    average_score = (
        round(total_score_sum / total_scored, 2) if total_scored > 0 else None
    )

    return {
        'labels': [str(score) for score in score_range],
        'datasets': [
            {
                'label': media_type.replace('_', ' ').title(),
                'data': [distribution[media_type][score] for score in score_range],
            }
            for media_type in distribution
        ],
        'average_score': average_score,
        'total_scored': total_scored,
    }


def get_timeline(user_media):
    """Build a timeline of media consumption organized by month-year.

    Args:
        user_media: Dict of media type to queryset

    Returns:
        Dict of month-year to list of media items
    """
    timeline = defaultdict(list)

    for media_type, queryset in user_media.items():
        if media_type == MediaTypes.TV.value:
            continue
        for media in queryset:
            if media.start_date and media.end_date:
                local_start_date = timezone.localdate(media.start_date)
                local_end_date = timezone.localdate(media.end_date)
                current_date = local_start_date
                while current_date <= local_end_date:
                    month_year = f'{calendar.month_name[current_date.month]} {current_date.year}'
                    timeline[month_year].append(media)
                    current_date += relativedelta(months=1)
                    current_date = current_date.replace(day=1)
            elif media.start_date:
                local_start_date = timezone.localdate(media.start_date)
                month_year = f'{calendar.month_name[local_start_date.month]} {local_start_date.year}'
                timeline[month_year].append(media)
            elif media.end_date:
                local_end_date = timezone.localdate(media.end_date)
                month_year = f'{calendar.month_name[local_end_date.month]} {local_end_date.year}'
                timeline[month_year].append(media)

    sorted_items = []
    for month_year, media_list in timeline.items():
        month_name, year_str = month_year.split()
        year = int(year_str)
        month = list(calendar.month_name).index(month_name)
        sorted_items.append((month_year, media_list, year, month))

    sorted_items.sort(key=lambda x: (x[2], x[3]), reverse=True)

    result = {}
    for month_year, media_list, _, _ in sorted_items:
        result[month_year] = sorted(
            media_list,
            key=lambda m: timezone.localdate(m.end_date or m.start_date),
            reverse=True,
        )
    return result


def calculate_streaks(date_counts, end_date):
    """Calculate current and longest activity streaks.

    Args:
        date_counts: Dict of date to count
        end_date: The end date to check against

    Returns:
        Tuple of (current_streak, longest_streak)
    """
    active_dates = sorted(
        [date for date, count in date_counts.items() if count > 0],
        reverse=True,
    )

    if not active_dates:
        return 0, 0

    longest_streak = 1
    streak_count = 1

    is_current = active_dates[0] == end_date
    current_streak = 1 if is_current else 0

    for i in range(1, len(active_dates)):
        if (active_dates[i - 1] - active_dates[i]).days == 1:
            streak_count += 1
            if is_current:
                current_streak += 1
        else:
            longest_streak = max(longest_streak, streak_count)
            streak_count = 1
            if is_current:
                is_current = False

    longest_streak = max(longest_streak, streak_count)

    return current_streak, longest_streak


def get_activity_level(count):
    """Calculate intensity level (0-4) based on count.

    Args:
        count: Number of activities

    Returns:
        Level from 0-4
    """
    thresholds = [0, 3, 6, 9]
    for i, threshold in enumerate(thresholds):
        if count <= threshold:
            return i
    return 4
