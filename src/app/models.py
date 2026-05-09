"""Core models for media tracking."""

import uuid

from django.conf import settings
from django.core.validators import (
    DecimalValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint

from app.helpers import minutes_to_hhmm


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
