"""Core models for media tracking."""

import uuid

from django.apps import apps
from django.conf import settings
from django.core.validators import (
    DecimalValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import (
    CheckConstraint,
    Count,
    F,
    Prefetch,
    Q,
    UniqueConstraint,
    Window,
)
from django.db.models.functions import Lower, RowNumber

from app.helpers import minutes_to_hhmm


class MediaManager(models.Manager):
    """Custom manager for media models."""

    def get_media_list(self, user, media_type, status_filter, sort_filter, search=None):
        """Get media list based on filters, sorting and search."""
        import users.models as users_models

        model = apps.get_model(app_label='app', model_name=media_type)
        queryset = model.objects.filter(user=user.id)

        if status_filter != users_models.MediaStatusChoices.ALL:
            queryset = queryset.filter(status=status_filter)

        if search:
            queryset = queryset.filter(item__title__icontains=search)

        queryset = queryset.annotate(
            repeats=Window(
                expression=Count('id'),
                partition_by=[F('item')],
            ),
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F('item')],
                order_by=F('created_at').desc(),
            ),
        ).filter(row_number=1)

        queryset = queryset.select_related('item')
        queryset = self._apply_prefetch_related(queryset, media_type)

        if sort_filter:
            return self._sort_media_list(queryset, sort_filter, media_type)
        return queryset

    def _apply_prefetch_related(self, queryset, media_type):
        """Apply appropriate prefetch_related based on media type."""
        if media_type == MediaTypes.TV.value:
            return queryset.prefetch_related(
                Prefetch(
                    'seasons',
                    queryset=Season.objects.select_related('item'),
                ),
                Prefetch(
                    'seasons__episodes',
                    queryset=Episode.objects.select_related('item'),
                ),
            )

        if media_type == MediaTypes.SEASON.value:
            return queryset.prefetch_related(
                Prefetch(
                    'episodes',
                    queryset=Episode.objects.select_related('item'),
                ),
            )

        return queryset

    def _sort_media_list(self, queryset, sort_filter, media_type=None):
        """Sort media list using SQL sorting with annotations."""
        if media_type == MediaTypes.TV.value:
            return self._sort_tv_media_list(queryset, sort_filter)
        if media_type == MediaTypes.SEASON.value:
            return self._sort_season_media_list(queryset, sort_filter)

        return self._sort_generic_media_list(queryset, sort_filter)

    def _sort_tv_media_list(self, queryset, sort_filter):
        """Sort TV media list based on the sort criteria."""
        if sort_filter == 'start_date':
            queryset = queryset.annotate(
                calculated_start_date=models.Min(
                    'seasons__episodes__end_date',
                    filter=models.Q(seasons__item__season_number__gt=0),
                ),
            )
            return queryset.order_by(
                models.F('calculated_start_date').asc(nulls_last=True),
                Lower('item__title'),
            )

        if sort_filter == 'end_date':
            queryset = queryset.annotate(
                calculated_end_date=models.Max(
                    'seasons__episodes__end_date',
                    filter=models.Q(seasons__item__season_number__gt=0),
                ),
            )
            return queryset.order_by(
                models.F('calculated_end_date').desc(nulls_last=True),
                Lower('item__title'),
            )

        if sort_filter == 'progress':
            queryset = queryset.annotate(
                calculated_progress=models.Count(
                    'seasons__episodes',
                    filter=models.Q(seasons__item__season_number__gt=0),
                ),
            )
            return queryset.order_by(
                '-calculated_progress',
                Lower('item__title'),
            )

        return self._sort_generic_media_list(queryset, sort_filter)

    def _sort_season_media_list(self, queryset, sort_filter):
        """Sort Season media list based on the sort criteria."""
        if sort_filter == 'start_date':
            queryset = queryset.annotate(
                calculated_start_date=models.Min('episodes__end_date'),
            )
            return queryset.order_by(
                models.F('calculated_start_date').asc(nulls_last=True),
                Lower('item__title'),
            )

        if sort_filter == 'end_date':
            queryset = queryset.annotate(
                calculated_end_date=models.Max('episodes__end_date'),
            )
            return queryset.order_by(
                models.F('calculated_end_date').desc(nulls_last=True),
                Lower('item__title'),
            )

        if sort_filter == 'progress':
            queryset = queryset.annotate(
                calculated_progress=models.Max('episodes__item__episode_number'),
            )
            return queryset.order_by(
                '-calculated_progress',
                Lower('item__title'),
            )

        return self._sort_generic_media_list(queryset, sort_filter)

    def _sort_generic_media_list(self, queryset, sort_filter):
        """Apply generic sorting logic for all media types."""
        if sort_filter in ('start_date', 'end_date'):
            if sort_filter == 'start_date':
                return queryset.order_by(
                    models.F(sort_filter).asc(nulls_last=True),
                    Lower('item__title'),
                )
            return queryset.order_by(
                models.F(sort_filter).desc(nulls_last=True),
                Lower('item__title'),
            )

        item_fields = [f.name for f in Item._meta.fields]
        if sort_filter in item_fields:
            if sort_filter == 'title':
                return queryset.order_by(Lower('item__title'))
            return queryset.order_by(
                f'-item__{sort_filter}',
                Lower('item__title'),
            )

        return queryset.order_by(
            models.F(sort_filter).desc(nulls_last=True),
            Lower('item__title'),
        )


class Sources(models.TextChoices):
    """Choices for the source of the item."""

    TMDB = 'tmdb', 'The Movie Database'
    MAL = 'mal', 'MyAnimeList'
    MANGAUPDATES = 'mangaupdates', 'MangaUpdates'
    IGDB = 'igdb', 'Internet Game Database'
    OPENLIBRARY = 'openlibrary', 'Open Library'
    HARDCOVER = 'hardcover', 'Hardcover'
    COMICVINE = 'comicvine', 'Comic Vine'
    BGG = 'bgg', 'BoardGameGeek'
    MANUAL = 'manual', 'Manual'


class MediaTypes(models.TextChoices):
    """Choices for the media type of the item."""

    TV = 'tv', 'TV Show'
    SEASON = 'season', 'TV Season'
    EPISODE = 'episode', 'Episode'
    MOVIE = 'movie', 'Movie'
    ANIME = 'anime', 'Anime'
    MANGA = 'manga', 'Manga'
    GAME = 'game', 'Game'
    BOOK = 'book', 'Book'
    COMIC = 'comic', 'Comic'
    BOARDGAME = 'boardgame', 'Boardgame'


class Status(models.TextChoices):
    """Choices for item status."""

    COMPLETED = 'Completed', 'Completed'
    IN_PROGRESS = 'In progress', 'In Progress'
    PLANNING = 'Planning', 'Planning'
    PAUSED = 'Paused', 'Paused'
    DROPPED = 'Dropped', 'Dropped'


class Item(models.Model):
    """Model to store basic information about media items."""

    media_id = models.CharField(max_length=36)
    source = models.CharField(
        max_length=20,
        choices=Sources,
    )
    media_type = models.CharField(
        max_length=10,
        choices=MediaTypes,
        default=MediaTypes.MOVIE.value,
    )
    title = models.TextField()
    image = models.URLField()
    season_number = models.PositiveIntegerField(null=True, blank=True)
    episode_number = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        """Meta options for the model."""

        constraints = [
            UniqueConstraint(
                fields=['media_id', 'source', 'media_type'],
                condition=Q(season_number__isnull=True, episode_number__isnull=True),
                name='unique_item_without_season_episode',
            ),
            UniqueConstraint(
                fields=['media_id', 'source', 'media_type', 'season_number'],
                condition=Q(season_number__isnull=False, episode_number__isnull=True),
                name='unique_item_with_season',
            ),
            UniqueConstraint(
                fields=[
                    'media_id',
                    'source',
                    'media_type',
                    'season_number',
                    'episode_number',
                ],
                condition=Q(season_number__isnull=False, episode_number__isnull=False),
                name='unique_item_with_season_episode',
            ),
            CheckConstraint(
                condition=Q(
                    media_type=MediaTypes.SEASON.value,
                    season_number__isnull=False,
                    episode_number__isnull=True,
                )
                | ~Q(media_type=MediaTypes.SEASON.value),
                name='season_number_required_for_season',
            ),
            CheckConstraint(
                condition=Q(
                    media_type=MediaTypes.EPISODE.value,
                    season_number__isnull=False,
                    episode_number__isnull=False,
                )
                | ~Q(media_type=MediaTypes.EPISODE.value),
                name='season_and_episode_required_for_episode',
            ),
            CheckConstraint(
                condition=Q(
                    ~Q(
                        media_type__in=[
                            MediaTypes.SEASON.value,
                            MediaTypes.EPISODE.value,
                        ],
                    ),
                    season_number__isnull=True,
                    episode_number__isnull=True,
                )
                | Q(media_type__in=[MediaTypes.SEASON.value, MediaTypes.EPISODE.value]),
                name='no_season_episode_for_other_types',
            ),
            CheckConstraint(
                condition=Q(source__in=Sources.values),
                name='%(app_label)s_%(class)s_source_valid',
            ),
            CheckConstraint(
                condition=Q(media_type__in=MediaTypes.values),
                name='%(app_label)s_%(class)s_media_type_valid',
            ),
        ]
        ordering = ['media_id']

    def __str__(self):
        """Return the name of the item."""
        name = self.title
        if self.season_number is not None:
            name += f' S{self.season_number}'
            if self.episode_number is not None:
                name += f'E{self.episode_number}'
        return name

    @classmethod
    def generate_manual_id(cls):
        """Generate a new ID for manual items using UUID."""
        return str(uuid.uuid4())


class Media(models.Model):
    """Abstract model for all media types."""

    created_at = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.DecimalField(
        null=True,
        blank=True,
        max_digits=3,
        decimal_places=1,
        validators=[
            DecimalValidator(3, 1),
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )
    progress = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.COMPLETED.value,
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        """Meta options for the model."""

        abstract = True
        ordering = ['user', 'item', '-created_at']

    def __str__(self):
        """Return the title of the media."""
        return str(self.item)

    @property
    def formatted_score(self):
        """Return as int if score is 10.0 or 0.0, otherwise show decimal."""
        if self.score is not None:
            if self.score in (10, 0):
                return int(self.score)
            return self.score
        return None

    @property
    def formatted_progress(self):
        """Return the progress of the media in a formatted string."""
        return str(self.progress)

    def increase_progress(self):
        """Increase the progress of the media by one."""
        self.progress += 1
        self.save()

    def decrease_progress(self):
        """Decrease the progress of the media by one."""
        if self.progress > 0:
            self.progress -= 1
            self.save()


class BasicMedia(Media):
    """Model for basic media types with the MediaManager attached."""

    objects = MediaManager()


class Movie(Media):
    """Model for movies."""

    pass


class Anime(Media):
    """Model for anime."""

    pass


class Manga(Media):
    """Model for manga."""

    pass


class Game(Media):
    """Model for games with playtime tracking in minutes."""

    @property
    def formatted_progress(self):
        """Return progress in hours:minutes format."""
        return minutes_to_hhmm(self.progress)

    def increase_progress(self):
        """Increase the progress of the game by 30 minutes."""
        self.progress += 30
        self.save()

    def decrease_progress(self):
        """Decrease the progress of the game by 30 minutes."""
        if self.progress >= 30:
            self.progress -= 30
            self.save()
        elif self.progress > 0:
            self.progress = 0
            self.save()


class Book(Media):
    """Model for books."""

    pass


class Comic(Media):
    """Model for comics."""

    pass


class BoardGame(Media):
    """Model for board games."""

    pass


class TV(Media):
    """Model for TV shows."""

    class Meta:
        """Meta options for the model."""

        ordering = ['user', 'item']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'item'],
                name='%(app_label)s_%(class)s_unique_item_user',
            ),
        ]

    @property
    def progress(self):
        """Return the total episodes watched for the TV show."""
        return sum(
            season.progress
            for season in self.seasons.all()
            if season.item.season_number != 0
        )

    @property
    def last_watched(self):
        """Return the latest watched episode in SxxExx format."""
        watched_episodes = [
            {
                'season': season.item.season_number,
                'episode': episode.item.episode_number,
                'end_date': episode.end_date,
            }
            for season in self.seasons.all()
            if hasattr(season, 'episodes') and season.item.season_number != 0
            for episode in season.episodes.all()
            if episode.end_date is not None
        ]

        if not watched_episodes:
            return ''

        latest_episode = max(
            watched_episodes,
            key=lambda x: (x['end_date'], x['season'], x['episode']),
        )

        return f"S{latest_episode['season']:02d}E{latest_episode['episode']:02d}"


class Season(Media):
    """Model for seasons of TV shows."""

    related_tv = models.ForeignKey(
        TV,
        on_delete=models.CASCADE,
        related_name='seasons',
        null=True,
        blank=True,
    )

    class Meta:
        """Meta options for the model."""

        constraints = [
            models.UniqueConstraint(
                fields=['related_tv', 'item'],
                name='%(app_label)s_season_unique_tv_item',
            ),
        ]

    def __str__(self):
        """Return the title of the media and season number."""
        return f'{self.item.title} S{self.item.season_number}'

    @property
    def progress(self):
        """Return the current episode number of the season."""
        episodes = self.episodes.all()
        if not episodes:
            return 0

        sorted_episodes = sorted(
            episodes,
            key=lambda e: -e.item.episode_number,
        )
        return sorted_episodes[0].item.episode_number


class Episode(models.Model):
    """Model for episodes of a season."""

    created_at = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    related_season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name='episodes',
    )
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta options for the model."""

        ordering = [
            'related_season',
            'item__episode_number',
            '-end_date',
            '-created_at',
        ]

    def __str__(self):
        """Return the season and episode number."""
        return str(self.item)
