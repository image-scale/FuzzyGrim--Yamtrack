"""Tests for the statistics module."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from app.models import Item, MediaTypes, Movie, Sources, Status
from app.statistics import (
    calculate_streaks,
    get_activity_level,
    get_media_type_distribution,
    get_score_distribution,
    get_status_distribution,
    get_timeline,
    get_user_media,
)
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


class TestGetUserMedia:
    """Tests for get_user_media function."""

    def test_returns_user_media(self, user, movie_item):
        """Test that get_user_media returns user's media."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )

        user_media, media_count = get_user_media(user)

        assert 'movie' in user_media
        assert media_count['movie'] == 1
        assert media_count['total'] >= 1

    def test_returns_empty_for_no_media(self, user):
        """Test that get_user_media returns empty for user with no media."""
        user_media, media_count = get_user_media(user)

        assert media_count['total'] == 0

    def test_date_range_filter(self, user, movie_item, movie_item2):
        """Test that date range filter works."""
        now = timezone.now()
        old_date = now - timedelta(days=365)

        Movie.objects.create(
            item=movie_item,
            user=user,
            start_date=now - timedelta(days=5),
            end_date=now,
        )
        Movie.objects.create(
            item=movie_item2,
            user=user,
            start_date=old_date,
            end_date=old_date + timedelta(days=1),
        )

        user_media, media_count = get_user_media(
            user,
            start_date=now - timedelta(days=30),
            end_date=now,
        )

        assert media_count['movie'] == 1


class TestGetMediaTypeDistribution:
    """Tests for get_media_type_distribution function."""

    def test_formats_chart_data(self):
        """Test that distribution formats data correctly."""
        media_count = {
            'movie': 5,
            'anime': 3,
            'total': 8,
        }

        chart_data = get_media_type_distribution(media_count)

        assert 'labels' in chart_data
        assert 'datasets' in chart_data
        assert len(chart_data['labels']) == 2
        assert 5 in chart_data['datasets'][0]['data']
        assert 3 in chart_data['datasets'][0]['data']

    def test_excludes_zero_counts(self):
        """Test that zero counts are excluded."""
        media_count = {
            'movie': 5,
            'anime': 0,
            'total': 5,
        }

        chart_data = get_media_type_distribution(media_count)

        assert len(chart_data['labels']) == 1
        assert 'Movie' in chart_data['labels']

    def test_excludes_total(self):
        """Test that total is excluded from distribution."""
        media_count = {
            'movie': 5,
            'total': 5,
        }

        chart_data = get_media_type_distribution(media_count)

        assert 'Total' not in chart_data['labels']


class TestGetStatusDistribution:
    """Tests for get_status_distribution function."""

    def test_counts_by_status(self, user, movie_item, movie_item2):
        """Test that status distribution counts correctly."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )
        Movie.objects.create(
            item=movie_item2,
            user=user,
            status=Status.IN_PROGRESS.value,
        )

        user_media = {'movie': Movie.objects.filter(user=user)}
        distribution = get_status_distribution(user_media)

        assert distribution['total_completed'] == 1
        assert 'datasets' in distribution


class TestGetScoreDistribution:
    """Tests for get_score_distribution function."""

    def test_calculates_average(self, user, movie_item, movie_item2):
        """Test that score distribution calculates average."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            score=Decimal('8.0'),
        )
        Movie.objects.create(
            item=movie_item2,
            user=user,
            score=Decimal('6.0'),
        )

        user_media = {'movie': Movie.objects.filter(user=user)}
        distribution = get_score_distribution(user_media)

        assert distribution['average_score'] == 7.0
        assert distribution['total_scored'] == 2

    def test_handles_no_scores(self, user, movie_item):
        """Test that score distribution handles no scores."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            score=None,
        )

        user_media = {'movie': Movie.objects.filter(user=user)}
        distribution = get_score_distribution(user_media)

        assert distribution['average_score'] is None
        assert distribution['total_scored'] == 0


class TestGetTimeline:
    """Tests for get_timeline function."""

    def test_organizes_by_month(self, user, movie_item, movie_item2):
        """Test that timeline organizes media by month."""
        now = timezone.now()
        Movie.objects.create(
            item=movie_item,
            user=user,
            start_date=now,
            end_date=now,
        )
        old_date = now - timedelta(days=60)
        Movie.objects.create(
            item=movie_item2,
            user=user,
            start_date=old_date,
            end_date=old_date,
        )

        user_media = {'movie': Movie.objects.filter(user=user)}
        timeline = get_timeline(user_media)

        assert len(timeline) >= 1


class TestCalculateStreaks:
    """Tests for calculate_streaks function."""

    def test_current_streak(self):
        """Test current streak calculation."""
        today = date.today()
        date_counts = {
            today: 1,
            today - timedelta(days=1): 1,
            today - timedelta(days=2): 1,
        }

        current, longest = calculate_streaks(date_counts, today)

        assert current == 3
        assert longest == 3

    def test_broken_streak(self):
        """Test streak calculation with gap."""
        today = date.today()
        date_counts = {
            today: 1,
            today - timedelta(days=2): 1,
            today - timedelta(days=3): 1,
        }

        current, longest = calculate_streaks(date_counts, today)

        assert current == 1
        assert longest == 2

    def test_no_current_streak(self):
        """Test when today has no activity."""
        today = date.today()
        date_counts = {
            today - timedelta(days=1): 1,
            today - timedelta(days=2): 1,
        }

        current, longest = calculate_streaks(date_counts, today)

        assert current == 0
        assert longest == 2

    def test_empty_activity(self):
        """Test with no activity."""
        today = date.today()
        date_counts = {}

        current, longest = calculate_streaks(date_counts, today)

        assert current == 0
        assert longest == 0


class TestGetActivityLevel:
    """Tests for get_activity_level function."""

    def test_level_zero(self):
        """Test level 0 for no activity."""
        assert get_activity_level(0) == 0

    def test_level_one(self):
        """Test level 1 for low activity."""
        assert get_activity_level(2) == 1

    def test_level_two(self):
        """Test level 2 for medium activity."""
        assert get_activity_level(5) == 2

    def test_level_three(self):
        """Test level 3 for high activity."""
        assert get_activity_level(8) == 3

    def test_level_four(self):
        """Test level 4 for very high activity."""
        assert get_activity_level(15) == 4
