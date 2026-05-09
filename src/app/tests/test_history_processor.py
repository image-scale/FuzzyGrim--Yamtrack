"""Tests for the history processor functions."""

from django.test import TestCase

from app import config
from app.history_processor import format_description
from app.models import MediaTypes, Status


class ConfigVerbTests(TestCase):
    """Tests for config.get_verb function."""

    def test_get_verb_covers_all_media_types(self):
        """Test that get_verb covers all media types defined in MediaTypes."""
        for media_type in MediaTypes:
            try:
                config.get_verb(media_type.value, past_tense=False)
                config.get_verb(media_type.value, past_tense=True)
            except KeyError:
                self.fail(f'Media type {media_type.name} not defined in get_verb')

    def test_get_verb_watch_types(self):
        """Test get_verb returns watch/watched for visual media."""
        assert config.get_verb(MediaTypes.TV.value, past_tense=False) == 'watch'
        assert config.get_verb(MediaTypes.TV.value, past_tense=True) == 'watched'
        assert config.get_verb(MediaTypes.MOVIE.value, past_tense=False) == 'watch'
        assert config.get_verb(MediaTypes.ANIME.value, past_tense=True) == 'watched'

    def test_get_verb_read_types(self):
        """Test get_verb returns read/read for reading media."""
        assert config.get_verb(MediaTypes.MANGA.value, past_tense=False) == 'read'
        assert config.get_verb(MediaTypes.MANGA.value, past_tense=True) == 'read'
        assert config.get_verb(MediaTypes.BOOK.value, past_tense=False) == 'read'

    def test_get_verb_play_types(self):
        """Test get_verb returns play/played for game media."""
        assert config.get_verb(MediaTypes.GAME.value, past_tense=False) == 'play'
        assert config.get_verb(MediaTypes.GAME.value, past_tense=True) == 'played'
        assert config.get_verb(MediaTypes.BOARDGAME.value, past_tense=False) == 'play'


class ConfigUnitTests(TestCase):
    """Tests for config.get_unit function."""

    def test_get_unit_episode(self):
        """Test get_unit returns Episode for episode-based media."""
        assert config.get_unit(MediaTypes.SEASON.value, short=False) == 'Episode'
        assert config.get_unit(MediaTypes.SEASON.value, short=True) == 'E'
        assert config.get_unit(MediaTypes.ANIME.value, short=False) == 'Episode'

    def test_get_unit_chapter(self):
        """Test get_unit returns Chapter for manga."""
        assert config.get_unit(MediaTypes.MANGA.value, short=False) == 'Chapter'
        assert config.get_unit(MediaTypes.MANGA.value, short=True) == '#'

    def test_get_unit_page(self):
        """Test get_unit returns Page for books."""
        assert config.get_unit(MediaTypes.BOOK.value, short=False) == 'Page'
        assert config.get_unit(MediaTypes.BOOK.value, short=True) == 'P'

    def test_get_unit_none(self):
        """Test get_unit returns None for media without units."""
        assert config.get_unit(MediaTypes.TV.value, short=False) is None
        assert config.get_unit(MediaTypes.MOVIE.value, short=True) is None


class FormatDescriptionStatusInitialTests(TestCase):
    """Tests for format_description with initial status changes."""

    def test_status_in_progress_tv(self):
        """Test format_description for initial in progress status."""
        result = format_description(
            'status',
            None,
            Status.IN_PROGRESS.value,
            MediaTypes.TV.value,
        )
        assert result == 'Marked as currently watching'

    def test_status_completed_manga(self):
        """Test format_description for initial completed status."""
        result = format_description(
            'status',
            None,
            Status.COMPLETED.value,
            MediaTypes.MANGA.value,
        )
        assert result == 'Marked as finished reading'

    def test_status_planning_game(self):
        """Test format_description for initial planning status."""
        result = format_description(
            'status',
            None,
            Status.PLANNING.value,
            MediaTypes.GAME.value,
        )
        assert result == 'Added to playing list'

    def test_status_dropped(self):
        """Test format_description for initial dropped status."""
        result = format_description(
            'status',
            None,
            Status.DROPPED.value,
            MediaTypes.BOOK.value,
        )
        assert result == 'Marked as dropped'

    def test_status_paused(self):
        """Test format_description for initial paused status."""
        result = format_description(
            'status',
            None,
            Status.PAUSED.value,
            MediaTypes.ANIME.value,
        )
        assert result == 'Marked as paused watching'


class FormatDescriptionStatusTransitionTests(TestCase):
    """Tests for format_description with status transitions."""

    def test_planning_to_in_progress(self):
        """Test status transition from planning to in progress."""
        result = format_description(
            'status',
            Status.PLANNING.value,
            Status.IN_PROGRESS.value,
            MediaTypes.TV.value,
        )
        assert result == 'Currently watching'

    def test_in_progress_to_completed(self):
        """Test status transition from in progress to completed."""
        result = format_description(
            'status',
            Status.IN_PROGRESS.value,
            Status.COMPLETED.value,
            MediaTypes.MANGA.value,
        )
        assert result == 'Finished reading'

    def test_in_progress_to_paused(self):
        """Test status transition from in progress to paused."""
        result = format_description(
            'status',
            Status.IN_PROGRESS.value,
            Status.PAUSED.value,
            MediaTypes.GAME.value,
        )
        assert result == 'Paused playing'

    def test_paused_to_in_progress(self):
        """Test status transition from paused to in progress."""
        result = format_description(
            'status',
            Status.PAUSED.value,
            Status.IN_PROGRESS.value,
            MediaTypes.BOOK.value,
        )
        assert result == 'Resumed reading'

    def test_in_progress_to_dropped(self):
        """Test status transition from in progress to dropped."""
        result = format_description(
            'status',
            Status.IN_PROGRESS.value,
            Status.DROPPED.value,
            MediaTypes.ANIME.value,
        )
        assert result == 'Stopped watching'

    def test_unknown_transition(self):
        """Test unknown status transition falls back to generic message."""
        result = format_description(
            'status',
            'Custom1',
            'Custom2',
            MediaTypes.TV.value,
        )
        assert result == 'Changed status from Custom1 to Custom2'


class FormatDescriptionScoreTests(TestCase):
    """Tests for format_description with score changes."""

    def test_initial_score(self):
        """Test format_description for initial score."""
        result = format_description('score', None, 8.5, MediaTypes.TV.value)
        assert result == 'Rated 8.5/10'

    def test_score_from_zero(self):
        """Test format_description for score from 0."""
        result = format_description('score', 0, 7.0, MediaTypes.ANIME.value)
        assert result == 'Rated 7.0/10'

    def test_score_change(self):
        """Test format_description for score change."""
        result = format_description('score', 6.5, 8.0, MediaTypes.MOVIE.value)
        assert result == 'Changed rating from 6.5 to 8.0'


class FormatDescriptionProgressTests(TestCase):
    """Tests for format_description with progress changes."""

    def test_initial_progress_game(self):
        """Test format_description for initial game progress."""
        result = format_description('progress', None, 120, MediaTypes.GAME.value)
        assert result == 'Played for 2h 00min'

    def test_initial_progress_book(self):
        """Test format_description for initial book progress."""
        result = format_description('progress', None, 5, MediaTypes.BOOK.value)
        assert result == 'Read up to page 5'

    def test_initial_progress_manga(self):
        """Test format_description for initial manga progress."""
        result = format_description('progress', None, 10, MediaTypes.MANGA.value)
        assert result == 'Read up to chapter 10'

    def test_progress_added_game(self):
        """Test format_description for game progress added."""
        result = format_description('progress', 60, 90, MediaTypes.GAME.value)
        assert result == 'Added 30min of playtime'

    def test_progress_removed_game(self):
        """Test format_description for game progress removed."""
        result = format_description('progress', 90, 60, MediaTypes.GAME.value)
        assert result == 'Removed 30min of playtime'

    def test_progress_change_book(self):
        """Test format_description for book progress change."""
        result = format_description('progress', 10, 15, MediaTypes.BOOK.value)
        assert result == 'Progress set to 15 pages'

    def test_progress_change_manga(self):
        """Test format_description for manga progress change."""
        result = format_description('progress', 5, 10, MediaTypes.MANGA.value)
        assert result == 'Progress set to 10 chapters'


class FormatDescriptionNotesTests(TestCase):
    """Tests for format_description with notes changes."""

    def test_initial_notes(self):
        """Test format_description for initial notes."""
        result = format_description('notes', None, 'Test notes')
        assert result == 'Added notes'

    def test_update_notes(self):
        """Test format_description for notes update."""
        result = format_description('notes', 'Old notes', 'New notes')
        assert result == 'Updated notes'

    def test_remove_notes(self):
        """Test format_description for notes removal."""
        result = format_description('notes', 'Old notes', '')
        assert result == 'Removed notes'


class FormatDescriptionGenericTests(TestCase):
    """Tests for format_description with generic field changes."""

    def test_generic_field_change(self):
        """Test format_description for generic field change."""
        result = format_description('custom_field', 'old', 'new')
        assert result == 'Updated custom field from old to new'

    def test_generic_field_initial(self):
        """Test format_description for generic initial field."""
        result = format_description('custom_field', None, 'value')
        assert result == 'Set custom field to value'
