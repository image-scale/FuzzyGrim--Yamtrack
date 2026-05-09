"""Tests for the MediaManager."""

from decimal import Decimal

import pytest
from django.utils import timezone

from app.models import (
    BasicMedia,
    Episode,
    Item,
    MediaTypes,
    Movie,
    Season,
    Sources,
    Status,
    TV,
)
from users.models import MediaStatusChoices, User


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


class TestGetMediaList:
    """Tests for MediaManager.get_media_list()."""

    def test_get_media_list_returns_user_media(self, user, movie_item):
        """Test that get_media_list returns media for the specified user."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert result[0].item == movie_item

    def test_get_media_list_filters_by_status(self, user, movie_item, movie_item2):
        """Test that get_media_list filters by status."""
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

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=Status.COMPLETED.value,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert result[0].status == Status.COMPLETED.value

    def test_get_media_list_all_status_returns_all(self, user, movie_item, movie_item2):
        """Test that ALL status filter returns all media."""
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

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 2

    def test_get_media_list_search_by_title(self, user, movie_item, movie_item2):
        """Test that search filters by title."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )
        Movie.objects.create(
            item=movie_item2,
            user=user,
            status=Status.COMPLETED.value,
        )

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
                search='Test',
            )
        )

        assert len(result) == 1
        assert result[0].item.title == 'Test Movie'

    def test_get_media_list_annotates_repeats(self, user, movie_item):
        """Test that get_media_list annotates repeat count."""
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )
        Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
        )

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert result[0].repeats == 2

    def test_get_media_list_returns_latest_entry(self, user, movie_item):
        """Test that get_media_list returns only the latest entry per item."""
        old_movie = Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.PLANNING.value,
            score=Decimal('5.0'),
        )
        new_movie = Movie.objects.create(
            item=movie_item,
            user=user,
            status=Status.COMPLETED.value,
            score=Decimal('8.5'),
        )

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert result[0].status == Status.COMPLETED.value
        assert result[0].score == Decimal('8.5')


class TestSortMediaList:
    """Tests for MediaManager sorting functionality."""

    def test_sort_by_title(self, user, movie_item, movie_item2):
        """Test sorting by title."""
        Movie.objects.create(item=movie_item, user=user)
        Movie.objects.create(item=movie_item2, user=user)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='title',
            )
        )

        assert result[0].item.title == 'Another Movie'
        assert result[1].item.title == 'Test Movie'

    def test_sort_by_score(self, user, movie_item, movie_item2):
        """Test sorting by score descending."""
        Movie.objects.create(item=movie_item, user=user, score=Decimal('7.5'))
        Movie.objects.create(item=movie_item2, user=user, score=Decimal('9.0'))

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='score',
            )
        )

        assert result[0].score == Decimal('9.0')
        assert result[1].score == Decimal('7.5')

    def test_sort_by_start_date(self, user, movie_item, movie_item2):
        """Test sorting by start date ascending."""
        now = timezone.now()
        earlier = now - timezone.timedelta(days=10)

        Movie.objects.create(item=movie_item, user=user, start_date=now)
        Movie.objects.create(item=movie_item2, user=user, start_date=earlier)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='start_date',
            )
        )

        assert result[0].item == movie_item2
        assert result[1].item == movie_item

    def test_sort_by_end_date(self, user, movie_item, movie_item2):
        """Test sorting by end date descending."""
        now = timezone.now()
        earlier = now - timezone.timedelta(days=10)

        Movie.objects.create(item=movie_item, user=user, end_date=earlier)
        Movie.objects.create(item=movie_item2, user=user, end_date=now)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='end_date',
            )
        )

        assert result[0].item == movie_item2
        assert result[1].item == movie_item

    def test_sort_handles_null_dates(self, user, movie_item, movie_item2):
        """Test that null dates are sorted last."""
        now = timezone.now()

        Movie.objects.create(item=movie_item, user=user, start_date=None)
        Movie.objects.create(item=movie_item2, user=user, start_date=now)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.MOVIE.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='start_date',
            )
        )

        assert result[0].item == movie_item2
        assert result[1].item == movie_item


class TestTVSorting:
    """Tests for TV-specific sorting."""

    @pytest.fixture
    def tv_item(self, db):
        """Create a TV item."""
        return Item.objects.create(
            media_id='tv123',
            source=Sources.TMDB.value,
            media_type=MediaTypes.TV.value,
            title='Test TV Show',
            image='https://example.com/tv.jpg',
        )

    @pytest.fixture
    def tv_item2(self, db):
        """Create a second TV item."""
        return Item.objects.create(
            media_id='tv456',
            source=Sources.TMDB.value,
            media_type=MediaTypes.TV.value,
            title='Another TV Show',
            image='https://example.com/tv2.jpg',
        )

    @pytest.fixture
    def setup_tv_with_episodes(self, db, user, tv_item):
        """Set up a TV show with seasons and episodes."""
        tv = TV.objects.create(item=tv_item, user=user)

        season_item = Item.objects.create(
            media_id=tv_item.media_id,
            source=Sources.TMDB.value,
            media_type=MediaTypes.SEASON.value,
            title=tv_item.title,
            image=tv_item.image,
            season_number=1,
        )
        season = Season.objects.create(
            item=season_item,
            user=user,
            related_tv=tv,
        )

        for i in range(1, 4):
            ep_item = Item.objects.create(
                media_id=tv_item.media_id,
                source=Sources.TMDB.value,
                media_type=MediaTypes.EPISODE.value,
                title=tv_item.title,
                image=tv_item.image,
                season_number=1,
                episode_number=i,
            )
            Episode.objects.create(
                item=ep_item,
                related_season=season,
                end_date=timezone.now() - timezone.timedelta(days=10 - i),
            )

        return tv

    def test_tv_sort_by_progress(self, user, setup_tv_with_episodes, tv_item2):
        """Test TV sorting by progress (episode count)."""
        TV.objects.create(item=tv_item2, user=user)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.TV.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='progress',
            )
        )

        assert len(result) == 2
        assert result[0].item.title == 'Test TV Show'

    def test_tv_sort_by_title(self, user, setup_tv_with_episodes, tv_item2):
        """Test TV sorting by title."""
        TV.objects.create(item=tv_item2, user=user)

        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.TV.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter='title',
            )
        )

        assert result[0].item.title == 'Another TV Show'
        assert result[1].item.title == 'Test TV Show'


class TestPrefetchRelated:
    """Tests for _apply_prefetch_related."""

    @pytest.fixture
    def tv_with_seasons(self, db, user):
        """Create a TV show with seasons and episodes."""
        tv_item = Item.objects.create(
            media_id='tvprefetch',
            source=Sources.TMDB.value,
            media_type=MediaTypes.TV.value,
            title='Prefetch Test',
            image='https://example.com/tv.jpg',
        )
        tv = TV.objects.create(item=tv_item, user=user)

        season_item = Item.objects.create(
            media_id='tvprefetch',
            source=Sources.TMDB.value,
            media_type=MediaTypes.SEASON.value,
            title='Prefetch Test',
            image='https://example.com/tv.jpg',
            season_number=1,
        )
        season = Season.objects.create(
            item=season_item,
            user=user,
            related_tv=tv,
        )

        ep_item = Item.objects.create(
            media_id='tvprefetch',
            source=Sources.TMDB.value,
            media_type=MediaTypes.EPISODE.value,
            title='Prefetch Test',
            image='https://example.com/tv.jpg',
            season_number=1,
            episode_number=1,
        )
        Episode.objects.create(item=ep_item, related_season=season)

        return tv

    def test_tv_prefetch_includes_seasons(self, user, tv_with_seasons):
        """Test that TV prefetch includes seasons."""
        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.TV.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert hasattr(result[0], '_prefetched_objects_cache')

    def test_season_prefetch_includes_episodes(self, user, tv_with_seasons):
        """Test that Season prefetch includes episodes."""
        result = list(
            BasicMedia.objects.get_media_list(
                user=user,
                media_type=MediaTypes.SEASON.value,
                status_filter=MediaStatusChoices.ALL,
                sort_filter=None,
            )
        )

        assert len(result) == 1
        assert hasattr(result[0], '_prefetched_objects_cache')
