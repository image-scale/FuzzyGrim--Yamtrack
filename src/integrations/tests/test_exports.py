"""Tests for export functionality."""

import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import (
    Anime,
    Book,
    Game,
    Item,
    Manga,
    MediaTypes,
    Movie,
    Sources,
    Status,
)
from integrations.exports import (
    Echo,
    generate_rows,
    get_model_fields,
    get_track_fields,
)


class EchoTests(TestCase):
    """Tests for the Echo class."""

    def test_echo_write_returns_value(self):
        """Test that Echo.write returns the value directly."""
        echo = Echo()
        result = echo.write('test value')
        assert result == 'test value'

    def test_echo_write_with_list(self):
        """Test that Echo.write works with list values."""
        echo = Echo()
        result = echo.write(['a', 'b', 'c'])
        assert result == ['a', 'b', 'c']


class GetModelFieldsTests(TestCase):
    """Tests for get_model_fields function."""

    def test_returns_item_fields(self):
        """Test that get_model_fields returns Item field names."""
        fields = get_model_fields(Item)

        assert 'media_id' in fields
        assert 'source' in fields
        assert 'media_type' in fields
        assert 'title' in fields

    def test_excludes_auto_fields(self):
        """Test that auto-created fields are excluded."""
        fields = get_model_fields(Item)

        assert 'id' not in fields

    def test_excludes_relation_fields(self):
        """Test that relation fields are excluded."""
        fields = get_model_fields(Item)

        assert 'movie' not in fields


class GetTrackFieldsTests(TestCase):
    """Tests for get_track_fields function."""

    def test_includes_common_fields(self):
        """Test that common tracking fields are included."""
        fields = get_track_fields()

        assert 'score' in fields
        assert 'progress' in fields
        assert 'status' in fields
        assert 'notes' in fields

    def test_date_fields_adjacent(self):
        """Test that start_date and end_date are adjacent."""
        fields = get_track_fields()

        if 'start_date' in fields and 'end_date' in fields:
            start_idx = fields.index('start_date')
            end_idx = fields.index('end_date')
            assert abs(start_idx - end_idx) == 1

    def test_timestamps_at_end(self):
        """Test that timestamp fields are at the end."""
        fields = get_track_fields()

        if 'created_at' in fields:
            assert fields.index('created_at') >= len(fields) - 2


class GenerateRowsTests(TestCase):
    """Tests for generate_rows function."""

    def setUp(self):
        """Create test user and media."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass',
        )

        item_movie = Item.objects.create(
            media_id='10494',
            source=Sources.TMDB.value,
            media_type=MediaTypes.MOVIE.value,
            title='Perfect Blue',
            image='https://image.url',
        )
        Movie.objects.create(
            item=item_movie,
            user=self.user,
            score=9,
            status=Status.COMPLETED.value,
            notes='Great movie',
        )

        item_anime = Item.objects.create(
            media_id='1',
            source=Sources.MAL.value,
            media_type=MediaTypes.ANIME.value,
            title='Cowboy Bebop',
            image='https://image.url',
        )
        Anime.objects.create(
            item=item_anime,
            user=self.user,
            status=Status.IN_PROGRESS.value,
            progress=10,
        )

        item_game = Item.objects.create(
            media_id='1',
            source=Sources.IGDB.value,
            media_type=MediaTypes.GAME.value,
            title='The Witcher 3',
            image='https://image.url',
        )
        Game.objects.create(
            item=item_game,
            user=self.user,
            status=Status.IN_PROGRESS.value,
            progress=120,
        )

    def test_generates_header_row(self):
        """Test that generate_rows yields a header row first."""
        rows = list(generate_rows(self.user))

        assert len(rows) > 0
        header = rows[0]
        assert 'media_id' in header
        assert 'title' in header
        assert 'score' in header
        assert 'status' in header

    def test_generates_data_rows(self):
        """Test that generate_rows yields data rows for user media."""
        rows = list(generate_rows(self.user))

        assert len(rows) > 1
        content = ''.join(rows)
        assert 'Perfect Blue' in content
        assert 'Cowboy Bebop' in content
        assert 'The Witcher 3' in content

    def test_game_progress_formatted(self):
        """Test that game progress is formatted as time."""
        rows = list(generate_rows(self.user))

        content = ''.join(rows)
        assert '2h 00min' in content

    def test_csv_format(self):
        """Test that output is valid CSV."""
        rows = list(generate_rows(self.user))
        csv_content = ''.join(rows)

        reader = csv.reader(StringIO(csv_content))
        rows_list = list(reader)

        assert len(rows_list) == 4
        header = rows_list[0]
        assert 'media_id' in header

    def test_empty_user(self):
        """Test generate_rows with user who has no media."""
        empty_user = get_user_model().objects.create_user(
            username='emptyuser',
            password='testpass',
        )

        rows = list(generate_rows(empty_user))

        assert len(rows) == 1


class ExportIntegrationTests(TestCase):
    """Integration tests for the export functionality."""

    def setUp(self):
        """Create test data."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass',
        )

        item_manga = Item.objects.create(
            media_id='1',
            source=Sources.MAL.value,
            media_type=MediaTypes.MANGA.value,
            title='Berserk',
            image='https://image.url',
        )
        Manga.objects.create(
            item=item_manga,
            user=self.user,
            status=Status.IN_PROGRESS.value,
            progress=300,
        )

        item_book = Item.objects.create(
            media_id='OL123',
            source=Sources.OPENLIBRARY.value,
            media_type=MediaTypes.BOOK.value,
            title='The Great Gatsby',
            image='https://image.url',
        )
        Book.objects.create(
            item=item_book,
            user=self.user,
            status=Status.COMPLETED.value,
            score=8.5,
        )

    def test_full_export_cycle(self):
        """Test complete export from generate_rows to CSV parsing."""
        rows = list(generate_rows(self.user))
        csv_content = ''.join(rows)

        reader = csv.DictReader(StringIO(csv_content))
        rows_list = list(reader)

        media_ids = {row['media_id'] for row in rows_list}
        assert '1' in media_ids
        assert 'OL123' in media_ids

        for row in rows_list:
            if row['title'] == 'Berserk':
                assert row['status'] == Status.IN_PROGRESS.value
            if row['title'] == 'The Great Gatsby':
                assert row['status'] == Status.COMPLETED.value
