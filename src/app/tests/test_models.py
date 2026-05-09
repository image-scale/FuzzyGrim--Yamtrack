"""Tests for the app models."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from app.models import Item, Media, MediaTypes, Sources, Status

User = get_user_model()


class SourcesEnumTest(TestCase):
    """Test cases for Sources enum."""

    def test_sources_values(self):
        """Test that all expected source values exist."""
        expected_sources = [
            'tmdb', 'mal', 'mangaupdates', 'igdb', 'openlibrary',
            'hardcover', 'comicvine', 'bgg', 'manual'
        ]
        for source in expected_sources:
            self.assertIn(source, Sources.values)

    def test_sources_labels(self):
        """Test that sources have human-readable labels."""
        self.assertEqual(Sources.TMDB.label, 'The Movie Database')
        self.assertEqual(Sources.MAL.label, 'MyAnimeList')
        self.assertEqual(Sources.MANUAL.label, 'Manual')


class MediaTypesEnumTest(TestCase):
    """Test cases for MediaTypes enum."""

    def test_media_types_values(self):
        """Test that all expected media type values exist."""
        expected_types = [
            'tv', 'season', 'episode', 'movie', 'anime',
            'manga', 'game', 'book', 'comic', 'boardgame'
        ]
        for media_type in expected_types:
            self.assertIn(media_type, MediaTypes.values)

    def test_media_types_labels(self):
        """Test that media types have human-readable labels."""
        self.assertEqual(MediaTypes.TV.label, 'TV Show')
        self.assertEqual(MediaTypes.MOVIE.label, 'Movie')
        self.assertEqual(MediaTypes.BOARDGAME.label, 'Boardgame')


class StatusEnumTest(TestCase):
    """Test cases for Status enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        expected_statuses = ['Completed', 'In progress', 'Planning', 'Paused', 'Dropped']
        for status in expected_statuses:
            self.assertIn(status, Status.values)

    def test_status_labels(self):
        """Test that statuses have labels."""
        self.assertEqual(Status.COMPLETED.label, 'Completed')
        self.assertEqual(Status.IN_PROGRESS.label, 'In Progress')


class ItemModelTest(TestCase):
    """Test cases for the Item model."""

    def test_item_creation_movie(self):
        """Test creating a movie item."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie',
            image='https://example.com/image.jpg',
        )
        self.assertEqual(item.title, 'Test Movie')
        self.assertEqual(item.media_type, MediaTypes.MOVIE.value)
        self.assertIsNone(item.season_number)
        self.assertIsNone(item.episode_number)

    def test_item_creation_season(self):
        """Test creating a season item with season number."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.SEASON.value,
            title='Test Show',
            image='https://example.com/image.jpg',
            season_number=1,
        )
        self.assertEqual(item.season_number, 1)
        self.assertIsNone(item.episode_number)

    def test_item_creation_episode(self):
        """Test creating an episode item with season and episode numbers."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.EPISODE.value,
            title='Test Show',
            image='https://example.com/image.jpg',
            season_number=1,
            episode_number=5,
        )
        self.assertEqual(item.season_number, 1)
        self.assertEqual(item.episode_number, 5)

    def test_item_str_simple(self):
        """Test string representation of simple item."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie',
            image='https://example.com/image.jpg',
        )
        self.assertEqual(str(item), 'Test Movie')

    def test_item_str_season(self):
        """Test string representation of season item."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.SEASON.value,
            title='Test Show',
            image='https://example.com/image.jpg',
            season_number=2,
        )
        self.assertEqual(str(item), 'Test Show S2')

    def test_item_str_episode(self):
        """Test string representation of episode item."""
        item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.EPISODE.value,
            title='Test Show',
            image='https://example.com/image.jpg',
            season_number=2,
            episode_number=3,
        )
        self.assertEqual(str(item), 'Test Show S2E3')

    def test_item_unique_constraint_basic(self):
        """Test unique constraint for basic items."""
        Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie',
            image='https://example.com/image.jpg',
        )
        with self.assertRaises(IntegrityError):
            Item.objects.create(
                media_id='12345',
                source=Sources.TMDB.value,
                media_type=MediaTypes.MOVIE.value,
                title='Test Movie 2',
                image='https://example.com/image2.jpg',
            )

    def test_item_unique_different_source(self):
        """Test that same media_id with different source is allowed."""
        Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie TMDB',
            image='https://example.com/image.jpg',
        )
        item2 = Item.objects.create(
            media_id='12345',
            source=Sources.MAL.value,
            media_type=MediaTypes.ANIME.value,
            title='Test Anime MAL',
            image='https://example.com/image.jpg',
        )
        self.assertIsNotNone(item2.pk)

    def test_generate_manual_id(self):
        """Test that generate_manual_id creates valid UUID strings."""
        manual_id = Item.generate_manual_id()
        self.assertEqual(len(manual_id), 36)  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        self.assertIn('-', manual_id)

    def test_generate_manual_id_unique(self):
        """Test that generate_manual_id creates unique IDs."""
        ids = [Item.generate_manual_id() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100)

    def test_item_ordering(self):
        """Test that items are ordered by media_id."""
        Item.objects.create(
            media_id='zzz',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Movie Z',
            image='https://example.com/image.jpg',
        )
        Item.objects.create(
            media_id='aaa',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Movie A',
            image='https://example.com/image.jpg',
        )
        items = list(Item.objects.values_list('media_id', flat=True))
        self.assertEqual(items, ['aaa', 'zzz'])


class TestMediaModel(TestCase):
    """Test cases for the Media abstract model using a concrete implementation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie',
            image='https://example.com/image.jpg',
        )


class MediaFormattedScoreTest(TestCase):
    """Test cases for Media.formatted_score property."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Test Movie',
            image='https://example.com/image.jpg',
        )

    def test_formatted_score_decimal_value(self):
        """Test formatted_score returns decimal for non-boundary scores."""
        from app.models import Media

        # Create a concrete Media subclass for testing
        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
            score=Decimal('7.5'),
        )
        self.assertEqual(media.formatted_score, Decimal('7.5'))

    def test_formatted_score_ten(self):
        """Test formatted_score returns int for score of 10."""
        from app.models import Media

        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
            score=Decimal('10.0'),
        )
        self.assertEqual(media.formatted_score, 10)
        self.assertIsInstance(media.formatted_score, int)

    def test_formatted_score_zero(self):
        """Test formatted_score returns int for score of 0."""
        from app.models import Media

        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
            score=Decimal('0.0'),
        )
        self.assertEqual(media.formatted_score, 0)
        self.assertIsInstance(media.formatted_score, int)

    def test_formatted_score_none(self):
        """Test formatted_score returns None when score is None."""
        from app.models import Media

        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
            score=None,
        )
        self.assertIsNone(media.formatted_score)


class MediaProgressMethodsTest(TestCase):
    """Test cases for Media progress methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.item = Item.objects.create(
            media_id='12345',
            source=Sources.TMDB.value,
            media_type=MediaTypes.ANIME.value,
            title='Test Anime',
            image='https://example.com/image.jpg',
        )

    def test_formatted_progress(self):
        """Test formatted_progress returns string of progress."""
        from app.models import Media

        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
            progress=15,
        )
        self.assertEqual(media.formatted_progress, '15')

    def test_media_str(self):
        """Test Media __str__ returns item string."""
        from app.models import Media

        class ConcreteMedia(Media):
            class Meta:
                app_label = 'app'

        media = ConcreteMedia(
            item=self.item,
            user=self.user,
        )
        self.assertEqual(str(media), 'Test Anime')
