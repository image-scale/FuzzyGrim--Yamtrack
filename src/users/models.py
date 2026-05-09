"""Users models."""

import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models

from app.models import MediaTypes, Status


def generate_token():
    """Generate a secure user token."""
    return secrets.token_urlsafe(24)


class HomeSortChoices(models.TextChoices):
    """Choices for home page sort options."""

    UPCOMING = 'upcoming', 'Upcoming'
    RECENT = 'recent', 'Recent'
    COMPLETION = 'completion', 'Completion'
    EPISODES_LEFT = 'episodes_left', 'Episodes Left'
    TITLE = 'title', 'Title'


class MediaSortChoices(models.TextChoices):
    """Choices for media list sort options."""

    SCORE = 'score', 'Rating'
    TITLE = 'title', 'Title'
    PROGRESS = 'progress', 'Progress'
    START_DATE = 'start_date', 'Start Date'
    END_DATE = 'end_date', 'End Date'


class MediaStatusChoices(models.TextChoices):
    """Choices for media list status options."""

    ALL = 'All', 'All'
    COMPLETED = Status.COMPLETED.value, Status.COMPLETED.label
    IN_PROGRESS = Status.IN_PROGRESS.value, Status.IN_PROGRESS.label
    PLANNING = Status.PLANNING.value, Status.PLANNING.label
    PAUSED = Status.PAUSED.value, Status.PAUSED.label
    DROPPED = Status.DROPPED.value, Status.DROPPED.label


class LayoutChoices(models.TextChoices):
    """Choices for media list layout options."""

    GRID = 'grid', 'Grid'
    TABLE = 'table', 'Table'


class CalendarLayoutChoices(models.TextChoices):
    """Choices for calendar layout options."""

    GRID = 'grid', 'Grid'
    LIST = 'list', 'List'


class ListSortChoices(models.TextChoices):
    """Choices for list sort options."""

    LAST_ITEM_ADDED = 'last_item_added', 'Last Item Added'
    NAME = 'name', 'Name'
    ITEMS_COUNT = 'items_count', 'Items Count'
    NEWEST_FIRST = 'newest_first', 'Newest First'


class ListDetailSortChoices(models.TextChoices):
    """Choices for list detail sort options."""

    DATE_ADDED = 'date_added', 'Date Added'
    TITLE = 'title', 'Title'
    MEDIA_TYPE = 'media_type', 'Media Type'


class QuickWatchDateChoices(models.TextChoices):
    """Choices for quick watch date behavior when bulk-marking media as completed."""

    CURRENT_DATE = 'current_date', 'Current Date'
    RELEASE_DATE = 'release_date', 'Release Date'
    NO_DATE = 'no_date', 'No Date'


class DateFormatChoices(models.TextChoices):
    """Choices for date format display."""

    ISO = 'Y-m-d', '2026-01-18 (ISO)'
    EUROPEAN = 'd/m/Y', '18/01/2026 (EU)'
    US = 'm/d/Y', '01/18/2026 (US)'
    LONG = 'M j, Y', 'Jan 18, 2026'


class TimeFormatChoices(models.TextChoices):
    """Choices for time format display."""

    HOUR_24 = 'H:i', '14:30 (24-hour)'
    HOUR_12 = 'g:i A', '2:30 PM (12-hour)'


EXCLUDED_SEARCH_TYPES = [MediaTypes.SEASON.value, MediaTypes.EPISODE.value]

VALID_SEARCH_TYPES = [
    value for value in MediaTypes.values if value not in EXCLUDED_SEARCH_TYPES
]


class User(AbstractUser):
    """Custom user model with media tracking preferences."""

    is_demo = models.BooleanField(default=False)

    last_search_type = models.CharField(
        max_length=10,
        default=MediaTypes.TV.value,
        choices=MediaTypes.choices,
    )

    home_sort = models.CharField(
        max_length=20,
        default=HomeSortChoices.UPCOMING,
        choices=HomeSortChoices,
    )

    # Media type preferences: TV Shows
    tv_enabled = models.BooleanField(default=True)
    tv_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    tv_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    tv_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: TV Seasons
    season_enabled = models.BooleanField(default=True)
    season_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    season_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    season_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Movies
    movie_enabled = models.BooleanField(default=True)
    movie_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    movie_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    movie_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Anime
    anime_enabled = models.BooleanField(default=True)
    anime_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.TABLE,
        choices=LayoutChoices,
    )
    anime_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    anime_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Manga
    manga_enabled = models.BooleanField(default=True)
    manga_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.TABLE,
        choices=LayoutChoices,
    )
    manga_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    manga_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Games
    game_enabled = models.BooleanField(default=True)
    game_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    game_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    game_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Books
    book_enabled = models.BooleanField(default=True)
    book_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    book_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    book_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Comics
    comic_enabled = models.BooleanField(default=True)
    comic_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    comic_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    comic_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Media type preferences: Board Games
    boardgame_enabled = models.BooleanField(default=True)
    boardgame_layout = models.CharField(
        max_length=20,
        default=LayoutChoices.GRID,
        choices=LayoutChoices,
    )
    boardgame_sort = models.CharField(
        max_length=20,
        default=MediaSortChoices.SCORE,
        choices=MediaSortChoices,
    )
    boardgame_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # UI preferences
    clickable_media_cards = models.BooleanField(
        default=False,
        help_text='Hide hover overlay on touch devices',
    )

    # Tracking settings
    quick_watch_date = models.CharField(
        max_length=20,
        default=QuickWatchDateChoices.CURRENT_DATE,
        choices=QuickWatchDateChoices,
        help_text='Date to use when bulk-marking media as completed',
    )

    date_format = models.CharField(
        max_length=20,
        default=DateFormatChoices.ISO,
        choices=DateFormatChoices,
        help_text='Preferred date display format',
    )
    time_format = models.CharField(
        max_length=20,
        default=TimeFormatChoices.HOUR_24,
        choices=TimeFormatChoices,
        help_text='Preferred time display format',
    )

    # Progress bar
    progress_bar = models.BooleanField(
        default=True,
        help_text='Show progress bar',
    )

    # Hide completed recommendations
    hide_completed_recommendations = models.BooleanField(
        default=False,
        help_text='Hide completed media in recommendations',
    )

    # Hide zero ratings
    hide_zero_rating = models.BooleanField(
        default=False,
        help_text='Hide zero ratings from media cards',
    )

    # Watch provider region
    watch_provider_region = models.CharField(
        max_length=5,
        default='UNSET',
        help_text='Region to show watch providers for',
    )

    # Calendar preferences
    calendar_layout = models.CharField(
        max_length=20,
        default=CalendarLayoutChoices.GRID,
        choices=CalendarLayoutChoices,
    )

    # Lists preferences
    lists_sort = models.CharField(
        max_length=20,
        default=ListSortChoices.LAST_ITEM_ADDED,
        choices=ListSortChoices,
    )
    list_detail_sort = models.CharField(
        max_length=20,
        default=ListDetailSortChoices.DATE_ADDED,
        choices=ListDetailSortChoices,
    )
    list_detail_status = models.CharField(
        max_length=20,
        default=MediaStatusChoices.ALL,
        choices=MediaStatusChoices,
    )

    # Notification settings
    notification_urls = models.TextField(
        blank=True,
        help_text='Apprise URLs for notifications',
    )
    release_notifications_enabled = models.BooleanField(
        default=True,
        help_text='Receive notifications for recently released media',
    )
    daily_digest_enabled = models.BooleanField(
        default=True,
        help_text='Receive a daily digest of upcoming releases',
    )

    # Integration settings
    token = models.CharField(
        max_length=32,
        unique=True,
        default=generate_token,
        help_text='Token for external integrations',
    )
    plex_usernames = models.TextField(
        blank=True,
        help_text='Comma-separated list of Plex usernames for webhook matching',
    )

    class Meta:
        """Meta options for the model."""

        ordering = ['username']

    def update_preference(self, field_name, new_value):
        """Update user preference if the new value is valid and different from current.

        Args:
            field_name: The name of the field to update
            new_value: The new value to set

        Returns:
            The value that was set (or the original value if invalid)
        """
        if new_value is None:
            return getattr(self, field_name)

        if field_name == 'last_search_type' and new_value not in VALID_SEARCH_TYPES:
            return getattr(self, field_name)

        field = self._meta.get_field(field_name)
        if hasattr(field, 'choices') and field.choices:
            valid_values = [choice[0] for choice in field.choices]
            if new_value not in valid_values:
                return getattr(self, field_name)

        current_value = getattr(self, field_name)

        if new_value != current_value:
            setattr(self, field_name, new_value)
            self.save(update_fields=[field_name])

        return new_value

    def resolve_watch_date(self, now, release_date):
        """Resolve the appropriate watch date based on user preference.

        Args:
            now: Pre-calculated current datetime
            release_date: The release/air date for the specific media item

        Returns:
            datetime or None based on user preference
        """
        if self.quick_watch_date == QuickWatchDateChoices.NO_DATE:
            return None

        if self.quick_watch_date == QuickWatchDateChoices.RELEASE_DATE:
            return release_date

        return now

    def get_enabled_media_types(self):
        """Return a list of enabled media type values based on user preferences."""
        enabled_types = []

        for media_type in MediaTypes.values:
            if media_type == MediaTypes.EPISODE.value:
                continue

            enabled_field = f'{media_type}_enabled'
            if getattr(self, enabled_field, False):
                enabled_types.append(media_type)

        return enabled_types

    def get_active_media_types(self):
        """Return a list of active media type values based on user preferences."""
        enabled_types = self.get_enabled_media_types()

        if (
            MediaTypes.TV.value in enabled_types
            and MediaTypes.SEASON.value not in enabled_types
        ):
            enabled_types.insert(0, MediaTypes.SEASON.value)

        return enabled_types

    def regenerate_token(self):
        """Regenerate the user's token."""
        self.token = generate_token()
        self.save(update_fields=['token'])
