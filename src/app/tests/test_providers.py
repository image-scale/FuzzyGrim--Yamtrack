"""Tests for the provider service layer."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models import MediaTypes, Sources
from app.providers.services import (
    ProviderAPIError,
    api_request,
    get_media_metadata,
    raise_not_found_error,
    search,
)


class TestProviderAPIError:
    """Tests for ProviderAPIError exception."""

    def test_error_with_known_provider(self):
        """Test error message with known provider."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_error = MagicMock()
        mock_error.response = mock_response

        error = ProviderAPIError(Sources.TMDB.value, mock_error)

        assert 'The Movie Database' in str(error)
        assert '500' in str(error)

    def test_error_with_details(self):
        """Test error message with details."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        mock_error = MagicMock()
        mock_error.response = mock_response

        error = ProviderAPIError(Sources.MAL.value, mock_error, 'Item not found')

        assert 'Item not found' in str(error)


class TestRaiseNotFoundError:
    """Tests for raise_not_found_error function."""

    def test_raises_provider_error(self):
        """Test that it raises ProviderAPIError."""
        with pytest.raises(ProviderAPIError) as exc_info:
            raise_not_found_error(Sources.IGDB.value, '123', 'game')

        assert exc_info.value.status_code == 404
        assert 'Game' in str(exc_info.value)


class TestApiRequest:
    """Tests for api_request function."""

    @patch('app.providers.services.requests.get')
    def test_successful_get_request(self, mock_get):
        """Test successful GET request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': 'test'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = api_request('test', 'GET', 'https://api.test.com')

        assert result == {'data': 'test'}
        mock_get.assert_called_once()

    @patch('app.providers.services.requests.post')
    def test_successful_post_request(self, mock_post):
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': 'ok'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = api_request('test', 'POST', 'https://api.test.com', params={'key': 'value'})

        assert result == {'result': 'ok'}
        mock_post.assert_called_once()

    @patch('app.providers.services.requests.get')
    def test_http_error_raises_provider_error(self, mock_get):
        """Test that HTTP error raises ProviderAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Server error'
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        with pytest.raises(ProviderAPIError):
            api_request('test', 'GET', 'https://api.test.com')


class TestGetMediaMetadata:
    """Tests for get_media_metadata function."""

    def test_manual_source_returns_metadata(self):
        """Test that manual source returns basic metadata."""
        result = get_media_metadata(
            MediaTypes.MOVIE.value,
            'manual-123',
            Sources.MANUAL.value,
        )

        assert result['media_id'] == 'manual-123'
        assert 'title' in result

    def test_manual_season_returns_metadata(self):
        """Test that manual season returns metadata."""
        result = get_media_metadata(
            MediaTypes.SEASON.value,
            'manual-123',
            Sources.MANUAL.value,
            season_numbers=[1],
        )

        assert result['media_id'] == 'manual-123'
        assert result['season_number'] == 1

    def test_manual_episode_returns_metadata(self):
        """Test that manual episode returns metadata."""
        result = get_media_metadata(
            MediaTypes.EPISODE.value,
            'manual-123',
            Sources.MANUAL.value,
            season_numbers=[1],
            episode_number=5,
        )

        assert result['media_id'] == 'manual-123'
        assert result['season_number'] == 1
        assert result['episode_number'] == 5

    def test_unknown_media_type_raises_error(self):
        """Test that unknown media type raises ValueError."""
        with pytest.raises(ValueError):
            get_media_metadata('unknown', '123', Sources.TMDB.value)


class TestSearch:
    """Tests for search function."""

    @patch('app.providers.services._search_movie')
    def test_search_dispatches_to_correct_handler(self, mock_search):
        """Test that search dispatches to correct handler."""
        mock_search.return_value = {
            'page': 1,
            'total_results': 0,
            'total_pages': 1,
            'results': [],
        }

        result = search(MediaTypes.MOVIE.value, 'test query', 1)

        mock_search.assert_called_once_with('test query', 1)
        assert 'results' in result

    def test_unknown_media_type_returns_empty(self):
        """Test that unknown media type returns empty results."""
        result = search('unknown_type', 'test', 1)

        assert result['total_results'] == 0
        assert result['results'] == []
