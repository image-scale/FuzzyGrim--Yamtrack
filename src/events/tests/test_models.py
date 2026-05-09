"""Tests for the events models."""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from app.models import Item, MediaTypes, Movie, Sources, Status
from events.models import Event, SentinelDatetime
from users.models import User


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
    )


@pytest.fixture
def movie_item(db):
    """Create a movie item."""
    return Item.objects.create(
        media_id='123',
        source=Sources.TMDB.value,
        media_type=MediaTypes.MOVIE.value,
        title='Test Movie',
        image='https://example.com/image.jpg',
    )


@pytest.fixture
def movie_item2(db):
    """Create a second movie item."""
    return Item.objects.create(
        media_id='456',
        source=Sources.TMDB.value,
        media_type=MediaTypes.MOVIE.value,
        title='Another Movie',
        image='https://example.com/image2.jpg',
    )


@pytest.fixture
def anime_item(db):
    """Create an anime item."""
    return Item.objects.create(
        media_id='789',
        source=Sources.MAL.value,
        media_type=MediaTypes.ANIME.value,
        title='Test Anime',
        image='https://example.com/anime.jpg',
    )


class TestEvent:
    """Tests for Event model."""

    def test_create_event(self, movie_item):
        """Test creating an event."""
        event_time = timezone.now() + timedelta(days=7)
        event = Event.objects.create(
            item=movie_item,
            datetime=event_time,
        )
        assert event.item == movie_item
        assert event.content_number is None
        assert event.notification_sent is False

    def test_create_event_with_content_number(self, anime_item):
        """Test creating an event with content number."""
        event_time = timezone.now() + timedelta(days=7)
        event = Event.objects.create(
            item=anime_item,
            content_number=5,
            datetime=event_time,
        )
        assert event.content_number == 5

    def test_event_str_without_content_number(self, movie_item):
        """Test event string representation without content number."""
        event = Event.objects.create(
            item=movie_item,
            datetime=timezone.now(),
        )
        assert str(event) == str(movie_item)

    def test_event_str_with_content_number(self, anime_item):
        """Test event string representation with content number."""
        event = Event.objects.create(
            item=anime_item,
            content_number=10,
            datetime=timezone.now(),
        )
        assert str(event) == f'{anime_item} #10'

    def test_readable_content_number(self, anime_item):
        """Test readable content number property."""
        event = Event.objects.create(
            item=anime_item,
            content_number=5,
            datetime=timezone.now(),
        )
        assert event.readable_content_number == '#5'

    def test_readable_content_number_none(self, movie_item):
        """Test readable content number when None."""
        event = Event.objects.create(
            item=movie_item,
            datetime=timezone.now(),
        )
        assert event.readable_content_number == ''


class TestEventUniqueConstraints:
    """Tests for Event unique constraints."""

    def test_unique_item_content_number(self, anime_item):
        """Test that same item+content_number cannot be duplicated."""
        event_time = timezone.now()
        Event.objects.create(
            item=anime_item,
            content_number=5,
            datetime=event_time,
        )

        with pytest.raises(IntegrityError):
            Event.objects.create(
                item=anime_item,
                content_number=5,
                datetime=event_time + timedelta(days=1),
            )

    def test_different_content_numbers_allowed(self, anime_item):
        """Test that same item with different content numbers is allowed."""
        event_time = timezone.now()
        Event.objects.create(
            item=anime_item,
            content_number=5,
            datetime=event_time,
        )
        Event.objects.create(
            item=anime_item,
            content_number=6,
            datetime=event_time + timedelta(days=1),
        )

        assert Event.objects.filter(item=anime_item).count() == 2

    def test_unique_item_null_content_number(self, movie_item, movie_item2):
        """Test that only one null content_number per item is allowed."""
        event_time = timezone.now()
        Event.objects.create(
            item=movie_item,
            content_number=None,
            datetime=event_time,
        )

        with pytest.raises(IntegrityError):
            Event.objects.create(
                item=movie_item,
                content_number=None,
                datetime=event_time + timedelta(days=1),
            )

    def test_different_items_null_content_number(self, movie_item, movie_item2):
        """Test that different items can have null content numbers."""
        event_time = timezone.now()
        Event.objects.create(
            item=movie_item,
            content_number=None,
            datetime=event_time,
        )
        Event.objects.create(
            item=movie_item2,
            content_number=None,
            datetime=event_time,
        )

        assert Event.objects.count() == 2


class TestSentinelTime:
    """Tests for sentinel time functionality."""

    def test_is_sentinel_time_true(self, movie_item):
        """Test is_sentinel_time returns True for sentinel time."""
        sentinel_time = timezone.now().replace(
            hour=SentinelDatetime.HOUR,
            minute=SentinelDatetime.MINUTE,
            second=SentinelDatetime.SECOND,
            microsecond=SentinelDatetime.MICROSECOND,
        )
        event = Event.objects.create(
            item=movie_item,
            datetime=sentinel_time,
        )
        assert event.is_sentinel_time is True

    def test_is_sentinel_time_false(self, movie_item):
        """Test is_sentinel_time returns False for regular time."""
        regular_time = timezone.now().replace(
            hour=10,
            minute=30,
            second=0,
            microsecond=0,
        )
        event = Event.objects.create(
            item=movie_item,
            datetime=regular_time,
        )
        assert event.is_sentinel_time is False

    def test_is_max_datetime(self, movie_item):
        """Test is_max_datetime for sentinel datetime."""
        max_datetime = timezone.make_aware(
            timezone.datetime(
                SentinelDatetime.YEAR,
                SentinelDatetime.MONTH,
                SentinelDatetime.DAY,
                12,
                0,
                0,
            )
        )
        event = Event.objects.create(
            item=movie_item,
            datetime=max_datetime,
        )
        assert event.is_max_datetime is True


class TestEventManager:
    """Tests for EventManager."""

    def test_get_user_events_returns_tracked_media(self, user, movie_item):
        """Test get_user_events returns events for tracked media."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.IN_PROGRESS.value,
        )
        event_time = timezone.now() + timedelta(days=3)
        Event.objects.create(item=movie_item, datetime=event_time)

        today = timezone.now().date()
        events = Event.objects.get_user_events(
            user,
            today,
            today + timedelta(days=7),
        )

        assert events.count() == 1

    def test_get_user_events_excludes_untracked(self, user, movie_item, movie_item2):
        """Test get_user_events excludes untracked media."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.IN_PROGRESS.value,
        )
        event_time = timezone.now() + timedelta(days=3)
        Event.objects.create(item=movie_item, datetime=event_time)
        Event.objects.create(item=movie_item2, datetime=event_time)

        today = timezone.now().date()
        events = Event.objects.get_user_events(
            user,
            today,
            today + timedelta(days=7),
        )

        assert events.count() == 1
        assert events[0].item == movie_item

    def test_get_user_events_excludes_dropped(self, user, movie_item):
        """Test get_user_events excludes dropped media."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.DROPPED.value,
        )
        event_time = timezone.now() + timedelta(days=3)
        Event.objects.create(item=movie_item, datetime=event_time)

        today = timezone.now().date()
        events = Event.objects.get_user_events(
            user,
            today,
            today + timedelta(days=7),
        )

        assert events.count() == 0

    def test_get_user_events_excludes_paused(self, user, movie_item):
        """Test get_user_events excludes paused media."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.PAUSED.value,
        )
        event_time = timezone.now() + timedelta(days=3)
        Event.objects.create(item=movie_item, datetime=event_time)

        today = timezone.now().date()
        events = Event.objects.get_user_events(
            user,
            today,
            today + timedelta(days=7),
        )

        assert events.count() == 0

    def test_get_user_events_date_range(self, user, movie_item):
        """Test get_user_events respects date range."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.IN_PROGRESS.value,
        )
        today = timezone.now().date()
        Event.objects.create(
            item=movie_item,
            datetime=timezone.make_aware(
                timezone.datetime.combine(today + timedelta(days=3), timezone.datetime.min.time())
            ),
        )

        events_in_range = Event.objects.get_user_events(
            user,
            today,
            today + timedelta(days=7),
        )
        events_out_of_range = Event.objects.get_user_events(
            user,
            today + timedelta(days=10),
            today + timedelta(days=14),
        )

        assert events_in_range.count() == 1
        assert events_out_of_range.count() == 0
