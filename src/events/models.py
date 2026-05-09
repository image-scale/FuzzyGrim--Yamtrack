"""Models for calendar events feature."""

from datetime import datetime

from django.db import models
from django.db.models import (
    Case,
    IntegerField,
    Q,
    UniqueConstraint,
    Value,
    When,
)
from django.utils import timezone

from app.models import Item, MediaTypes, Status

INACTIVE_TRACKING_STATUSES = [
    Status.PAUSED.value,
    Status.DROPPED.value,
]


class SentinelDatetime:
    """Sentinel time for events without a specific time."""

    YEAR = 9999
    MONTH = 12
    DAY = 31
    HOUR = 11
    MINUTE = 59
    SECOND = 59
    MICROSECOND = 999999


class EventManager(models.Manager):
    """Custom manager for the Event model."""

    def get_user_events(self, user, first_day, last_day):
        """Get all upcoming media events of the specified user.

        Args:
            user: The user to get events for
            first_day: Start date of the range
            last_day: End date of the range

        Returns:
            QuerySet of events for the user's tracked media
        """
        start_datetime = timezone.make_aware(
            datetime.combine(first_day, datetime.min.time()),
        )
        end_datetime = timezone.make_aware(
            datetime.combine(last_day, datetime.max.time()),
        )

        enabled_types = user.get_enabled_media_types()
        non_tv_types = [
            media_type
            for media_type in enabled_types
            if media_type not in [MediaTypes.TV.value, MediaTypes.SEASON.value]
        ]

        user_query = Q()
        active_status_query = Q()

        for media_type in non_tv_types:
            user_query |= Q(**{f'item__{media_type}__user': user})
            active_status_query &= ~Q(
                **{f'item__{media_type}__status__in': INACTIVE_TRACKING_STATUSES},
            )

        combined_query = user_query & active_status_query

        queryset = self.filter(
            combined_query,
            datetime__gte=start_datetime,
            datetime__lte=end_datetime,
        ).select_related('item')

        return self.sort_with_sentinel_last(queryset)

    def sort_with_sentinel_last(self, queryset):
        """Sort events with sentinel time last."""
        return queryset.annotate(
            is_sentinel=Case(
                When(
                    datetime__hour=SentinelDatetime.HOUR,
                    datetime__minute=SentinelDatetime.MINUTE,
                    datetime__second=SentinelDatetime.SECOND,
                    then=Value(1),
                ),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by('datetime__date', 'is_sentinel', 'datetime')


class Event(models.Model):
    """Calendar event model for tracking upcoming media releases."""

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    content_number = models.IntegerField(null=True, blank=True)
    datetime = models.DateTimeField()
    notification_sent = models.BooleanField(default=False)

    objects = EventManager()

    class Meta:
        """Meta class for Event model."""

        ordering = ['-datetime']
        constraints = [
            UniqueConstraint(
                fields=['item', 'content_number'],
                name='unique_item_content_number',
            ),
            UniqueConstraint(
                fields=['item'],
                condition=Q(content_number__isnull=True),
                name='unique_item_null_content_number',
            ),
        ]

    def __str__(self):
        """Return event title."""
        if self.content_number:
            return f'{self.item} #{self.content_number}'
        return str(self.item)

    @property
    def readable_content_number(self):
        """Return the content number in a readable format."""
        if self.content_number is None:
            return ''
        return f'#{self.content_number}'

    @property
    def is_sentinel_time(self):
        """Check if the event time is sentinel time."""
        return (
            self.datetime.hour == SentinelDatetime.HOUR
            and self.datetime.minute == SentinelDatetime.MINUTE
            and self.datetime.second == SentinelDatetime.SECOND
            and self.datetime.microsecond == SentinelDatetime.MICROSECOND
        )

    @property
    def is_max_datetime(self):
        """Check if the event datetime is the maximum sentinel datetime."""
        return (
            self.datetime.year == SentinelDatetime.YEAR
            and self.datetime.month == SentinelDatetime.MONTH
            and self.datetime.day == SentinelDatetime.DAY
        )
