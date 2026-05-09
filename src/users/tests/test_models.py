"""Tests for the users models."""

from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import MediaTypes
from users.models import (
    VALID_SEARCH_TYPES,
    HomeSortChoices,
    LayoutChoices,
    MediaSortChoices,
    MediaStatusChoices,
    QuickWatchDateChoices,
)

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_user_creation_with_defaults(self):
        """Test that a user is created with default preferences."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.home_sort, HomeSortChoices.UPCOMING)
        self.assertEqual(self.user.tv_layout, LayoutChoices.GRID)
        self.assertEqual(self.user.tv_sort, MediaSortChoices.SCORE)
        self.assertEqual(self.user.tv_status, MediaStatusChoices.ALL)
        self.assertTrue(self.user.tv_enabled)
        self.assertTrue(self.user.movie_enabled)
        self.assertTrue(self.user.anime_enabled)
        self.assertTrue(self.user.manga_enabled)
        self.assertTrue(self.user.game_enabled)
        self.assertTrue(self.user.book_enabled)
        self.assertFalse(self.user.is_demo)

    def test_user_ordering(self):
        """Test that users are ordered by username."""
        User.objects.create_user(username='alice', password='pass')
        User.objects.create_user(username='bob', password='pass')
        User.objects.create_user(username='charlie', password='pass')

        users = list(User.objects.values_list('username', flat=True))
        self.assertEqual(users, ['alice', 'bob', 'charlie', 'testuser'])

    def test_user_token_generated(self):
        """Test that a token is generated for new users."""
        self.assertIsNotNone(self.user.token)
        self.assertEqual(len(self.user.token), 32)

    def test_user_token_unique(self):
        """Test that tokens are unique across users."""
        user2 = User.objects.create_user(username='user2', password='pass')
        self.assertNotEqual(self.user.token, user2.token)


class UserUpdatePreferenceTest(TestCase):
    """Test cases for the User.update_preference method."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_update_preference_valid_value(self):
        """Test updating a preference with a valid value."""
        result = self.user.update_preference('home_sort', HomeSortChoices.RECENT)
        self.assertEqual(result, HomeSortChoices.RECENT)
        self.user.refresh_from_db()
        self.assertEqual(self.user.home_sort, HomeSortChoices.RECENT)

    def test_update_preference_invalid_value(self):
        """Test that invalid values are rejected."""
        original = self.user.home_sort
        result = self.user.update_preference('home_sort', 'invalid_value')
        self.assertEqual(result, original)
        self.user.refresh_from_db()
        self.assertEqual(self.user.home_sort, original)

    def test_update_preference_none_value(self):
        """Test that None values return current value."""
        original = self.user.tv_layout
        result = self.user.update_preference('tv_layout', None)
        self.assertEqual(result, original)

    def test_update_preference_same_value_no_save(self):
        """Test that same value doesn't trigger unnecessary save."""
        self.user.home_sort = HomeSortChoices.TITLE
        self.user.save()

        result = self.user.update_preference('home_sort', HomeSortChoices.TITLE)
        self.assertEqual(result, HomeSortChoices.TITLE)

    def test_update_preference_last_search_type_valid(self):
        """Test updating last_search_type with valid value."""
        result = self.user.update_preference('last_search_type', MediaTypes.MOVIE.value)
        self.assertEqual(result, MediaTypes.MOVIE.value)

    def test_update_preference_last_search_type_invalid(self):
        """Test that invalid search types (season, episode) are rejected."""
        original = self.user.last_search_type
        result = self.user.update_preference('last_search_type', MediaTypes.SEASON.value)
        self.assertEqual(result, original)

    def test_update_layout_preference(self):
        """Test updating layout preferences."""
        result = self.user.update_preference('movie_layout', LayoutChoices.TABLE)
        self.assertEqual(result, LayoutChoices.TABLE)
        self.user.refresh_from_db()
        self.assertEqual(self.user.movie_layout, LayoutChoices.TABLE)


class UserEnabledMediaTypesTest(TestCase):
    """Test cases for User.get_enabled_media_types method."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_all_media_types_enabled_by_default(self):
        """Test that all media types are enabled by default."""
        enabled = self.user.get_enabled_media_types()

        self.assertIn(MediaTypes.TV.value, enabled)
        self.assertIn(MediaTypes.MOVIE.value, enabled)
        self.assertIn(MediaTypes.ANIME.value, enabled)
        self.assertIn(MediaTypes.MANGA.value, enabled)
        self.assertIn(MediaTypes.GAME.value, enabled)
        self.assertIn(MediaTypes.BOOK.value, enabled)
        self.assertIn(MediaTypes.COMIC.value, enabled)
        self.assertIn(MediaTypes.BOARDGAME.value, enabled)
        self.assertIn(MediaTypes.SEASON.value, enabled)

    def test_episode_type_excluded(self):
        """Test that episode type is never included."""
        enabled = self.user.get_enabled_media_types()
        self.assertNotIn(MediaTypes.EPISODE.value, enabled)

    def test_disabled_media_type_not_in_list(self):
        """Test that disabled media types are not in the list."""
        self.user.movie_enabled = False
        self.user.save()

        enabled = self.user.get_enabled_media_types()
        self.assertNotIn(MediaTypes.MOVIE.value, enabled)
        self.assertIn(MediaTypes.TV.value, enabled)

    def test_multiple_disabled_types(self):
        """Test disabling multiple media types."""
        self.user.movie_enabled = False
        self.user.anime_enabled = False
        self.user.game_enabled = False
        self.user.save()

        enabled = self.user.get_enabled_media_types()
        self.assertNotIn(MediaTypes.MOVIE.value, enabled)
        self.assertNotIn(MediaTypes.ANIME.value, enabled)
        self.assertNotIn(MediaTypes.GAME.value, enabled)
        self.assertIn(MediaTypes.TV.value, enabled)
        self.assertIn(MediaTypes.MANGA.value, enabled)


class UserActiveMediaTypesTest(TestCase):
    """Test cases for User.get_active_media_types method."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_season_added_when_tv_enabled(self):
        """Test that season is added when TV is enabled."""
        active = self.user.get_active_media_types()
        self.assertIn(MediaTypes.SEASON.value, active)
        self.assertIn(MediaTypes.TV.value, active)

    def test_season_not_duplicated(self):
        """Test that season is not duplicated if already enabled."""
        active = self.user.get_active_media_types()
        season_count = active.count(MediaTypes.SEASON.value)
        self.assertEqual(season_count, 1)


class UserResolveWatchDateTest(TestCase):
    """Test cases for User.resolve_watch_date method."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.now = datetime(2024, 1, 15, 12, 0, 0)
        self.release_date = datetime(2024, 1, 10, 12, 0, 0)

    def test_current_date_preference(self):
        """Test that current date is returned when preference is CURRENT_DATE."""
        self.user.quick_watch_date = QuickWatchDateChoices.CURRENT_DATE
        result = self.user.resolve_watch_date(self.now, self.release_date)
        self.assertEqual(result, self.now)

    def test_release_date_preference(self):
        """Test that release date is returned when preference is RELEASE_DATE."""
        self.user.quick_watch_date = QuickWatchDateChoices.RELEASE_DATE
        result = self.user.resolve_watch_date(self.now, self.release_date)
        self.assertEqual(result, self.release_date)

    def test_no_date_preference(self):
        """Test that None is returned when preference is NO_DATE."""
        self.user.quick_watch_date = QuickWatchDateChoices.NO_DATE
        result = self.user.resolve_watch_date(self.now, self.release_date)
        self.assertIsNone(result)

    def test_release_date_none(self):
        """Test that None is returned when release_date is None and preference is RELEASE_DATE."""
        self.user.quick_watch_date = QuickWatchDateChoices.RELEASE_DATE
        result = self.user.resolve_watch_date(self.now, None)
        self.assertIsNone(result)


class UserRegenerateTokenTest(TestCase):
    """Test cases for User.regenerate_token method."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    def test_regenerate_token_creates_new_token(self):
        """Test that regenerate_token creates a new token."""
        old_token = self.user.token
        self.user.regenerate_token()
        self.assertNotEqual(self.user.token, old_token)
        self.assertEqual(len(self.user.token), 32)

    def test_regenerate_token_persists(self):
        """Test that the new token is persisted to database."""
        self.user.regenerate_token()
        new_token = self.user.token

        self.user.refresh_from_db()
        self.assertEqual(self.user.token, new_token)


class ValidSearchTypesTest(TestCase):
    """Test cases for VALID_SEARCH_TYPES constant."""

    def test_valid_search_types_excludes_season_and_episode(self):
        """Test that VALID_SEARCH_TYPES excludes season and episode."""
        self.assertNotIn(MediaTypes.SEASON.value, VALID_SEARCH_TYPES)
        self.assertNotIn(MediaTypes.EPISODE.value, VALID_SEARCH_TYPES)

    def test_valid_search_types_includes_main_types(self):
        """Test that VALID_SEARCH_TYPES includes main media types."""
        self.assertIn(MediaTypes.TV.value, VALID_SEARCH_TYPES)
        self.assertIn(MediaTypes.MOVIE.value, VALID_SEARCH_TYPES)
        self.assertIn(MediaTypes.ANIME.value, VALID_SEARCH_TYPES)
        self.assertIn(MediaTypes.MANGA.value, VALID_SEARCH_TYPES)
        self.assertIn(MediaTypes.GAME.value, VALID_SEARCH_TYPES)
        self.assertIn(MediaTypes.BOOK.value, VALID_SEARCH_TYPES)
