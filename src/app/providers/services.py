"""Provider service layer for external media database APIs."""

import logging
import time

import requests
from django.conf import settings

from app.models import MediaTypes, Sources

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = getattr(settings, 'REQUEST_TIMEOUT', 30)


class ProviderAPIError(Exception):
    """Exception raised when a provider API fails to respond."""

    def __init__(self, provider, error, details=None):
        """Initialize the exception with the provider name and error details."""
        self.provider = provider
        self.status_code = getattr(error.response, 'status_code', 500)

        try:
            provider_label = Sources(provider).label
        except ValueError:
            provider_label = provider.title()

        logger.error('%s error: %s', provider_label, getattr(error.response, 'text', str(error)))

        message = (
            f'There was an error contacting the {provider_label} API '
            f'(HTTP {self.status_code})'
        )
        if details:
            message += f': {details}'
        message += '. Check the logs for more details.'
        super().__init__(message)


def raise_not_found_error(provider, media_id, media_type='item'):
    """Raise a 404 ProviderAPIError for when a media item is not found.

    Args:
        provider: The provider source value (e.g., Sources.COMICVINE.value)
        media_id: The media ID that was not found
        media_type: The type of media (e.g., 'comic', 'game', 'book')
    """
    error_msg = f'{media_type.capitalize()} with ID {media_id} not found'
    logger.error('%s: %s', provider, error_msg)

    mock_response = type(
        'MockResponse',
        (object,),
        {
            'status_code': 404,
            'text': error_msg,
        },
    )()
    mock_error = requests.exceptions.HTTPError(response=mock_response)

    raise ProviderAPIError(provider, mock_error, error_msg)


def api_request(
    provider,
    method,
    url,
    params=None,
    data=None,
    headers=None,
    response_format='json',
):
    """Make a request to the API and return the response.

    Args:
        provider: Provider identifier for error messages
        method: HTTP method ('GET' or 'POST')
        url: Request URL
        params: Query params for GET, JSON body for POST
        data: Raw data for POST
        headers: Request headers
        response_format: 'json' (default) or 'xml' for XML parsing

    Returns:
        Parsed JSON dict or ElementTree for XML

    Raises:
        ProviderAPIError: When the API request fails
    """
    try:
        request_kwargs = {
            'url': url,
            'headers': headers,
            'timeout': REQUEST_TIMEOUT,
        }

        if method == 'GET':
            request_kwargs['params'] = params
            response = requests.get(**request_kwargs)
        elif method == 'POST':
            request_kwargs['data'] = data
            request_kwargs['json'] = params
            response = requests.post(**request_kwargs)
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')

        response.raise_for_status()

        if response_format == 'xml':
            from defusedxml import ElementTree
            return ElementTree.fromstring(response.text)
        return response.json()

    except requests.exceptions.HTTPError as error:
        error_resp = error.response
        status_code = error_resp.status_code if error_resp else 500

        if status_code == 429:
            seconds_to_wait = int(error_resp.headers.get('Retry-After', 5))
            logger.warning('Rate limited, waiting %s seconds', seconds_to_wait)
            time.sleep(seconds_to_wait + 1)
            logger.info('Retrying request')
            return api_request(
                provider,
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                response_format=response_format,
            )

        raise ProviderAPIError(provider, error) from None

    except requests.exceptions.RequestException as error:
        logger.error('%s request error: %s', provider, str(error))
        mock_response = type(
            'MockResponse',
            (object,),
            {
                'status_code': 500,
                'text': str(error),
            },
        )()
        mock_error = type(
            'MockError',
            (object,),
            {'response': mock_response},
        )()
        raise ProviderAPIError(provider, mock_error, str(error)) from None


def get_media_metadata(
    media_type,
    media_id,
    source,
    season_numbers=None,
    episode_number=None,
):
    """Return the metadata for the selected media.

    Args:
        media_type: The type of media
        media_id: The ID of the media
        source: The source provider
        season_numbers: Optional list of season numbers (for TV)
        episode_number: Optional episode number (for TV)

    Returns:
        Dict containing media metadata
    """
    from app.providers import manual

    if source == Sources.MANUAL.value:
        if media_type == MediaTypes.SEASON.value:
            return manual.season(media_id, season_numbers[0] if season_numbers else 1)
        if media_type == MediaTypes.EPISODE.value:
            return manual.episode(
                media_id,
                season_numbers[0] if season_numbers else 1,
                episode_number or 1,
            )
        if media_type == 'tv_with_seasons':
            media_type = MediaTypes.TV.value
        return manual.metadata(media_id, media_type)

    metadata_retrievers = {
        MediaTypes.ANIME.value: lambda: _get_anime_metadata(media_id),
        MediaTypes.MANGA.value: lambda: _get_manga_metadata(media_id, source),
        MediaTypes.TV.value: lambda: _get_tv_metadata(media_id),
        'tv_with_seasons': lambda: _get_tv_with_seasons_metadata(media_id, season_numbers),
        MediaTypes.SEASON.value: lambda: _get_season_metadata(media_id, season_numbers),
        MediaTypes.EPISODE.value: lambda: _get_episode_metadata(media_id, season_numbers, episode_number),
        MediaTypes.MOVIE.value: lambda: _get_movie_metadata(media_id),
        MediaTypes.GAME.value: lambda: _get_game_metadata(media_id),
        MediaTypes.BOOK.value: lambda: _get_book_metadata(media_id, source),
        MediaTypes.COMIC.value: lambda: _get_comic_metadata(media_id),
        MediaTypes.BOARDGAME.value: lambda: _get_boardgame_metadata(media_id),
    }

    retriever = metadata_retrievers.get(media_type)
    if retriever:
        return retriever()

    raise ValueError(f'Unknown media type: {media_type}')


def search(media_type, query, page, source=None):
    """Search for media based on the query and return the results.

    Args:
        media_type: The type of media to search for
        query: The search query
        page: The page number for pagination
        source: Optional source provider

    Returns:
        Dict containing search results with pagination
    """
    from app.helpers import format_search_response

    search_handlers = {
        MediaTypes.MANGA.value: lambda: _search_manga(query, page, source),
        MediaTypes.ANIME.value: lambda: _search_anime(query, page),
        MediaTypes.TV.value: lambda: _search_tv(query, page),
        MediaTypes.MOVIE.value: lambda: _search_movie(query, page),
        MediaTypes.SEASON.value: lambda: _search_tv(query, page),
        MediaTypes.EPISODE.value: lambda: _search_tv(query, page),
        MediaTypes.GAME.value: lambda: _search_game(query, page),
        MediaTypes.BOOK.value: lambda: _search_book(query, page, source),
        MediaTypes.COMIC.value: lambda: _search_comic(query, page),
        MediaTypes.BOARDGAME.value: lambda: _search_boardgame(query, page),
    }

    handler = search_handlers.get(media_type)
    if handler:
        return handler()

    return format_search_response(page, 20, 0, [])


def _get_anime_metadata(media_id):
    """Get anime metadata from MAL."""
    from app.providers import mal
    return mal.anime(media_id)


def _get_manga_metadata(media_id, source):
    """Get manga metadata from appropriate provider."""
    from app.providers import mal, mangaupdates
    if source == Sources.MANGAUPDATES.value:
        return mangaupdates.manga(media_id)
    return mal.manga(media_id)


def _get_tv_metadata(media_id):
    """Get TV metadata from TMDB."""
    from app.providers import tmdb
    return tmdb.tv(media_id)


def _get_tv_with_seasons_metadata(media_id, season_numbers):
    """Get TV with seasons metadata from TMDB."""
    from app.providers import tmdb
    return tmdb.tv_with_seasons(media_id, season_numbers)


def _get_season_metadata(media_id, season_numbers):
    """Get season metadata from TMDB."""
    from app.providers import tmdb
    result = tmdb.tv_with_seasons(media_id, season_numbers)
    return result.get(f'season/{season_numbers[0]}', {})


def _get_episode_metadata(media_id, season_numbers, episode_number):
    """Get episode metadata from TMDB."""
    from app.providers import tmdb
    return tmdb.episode(media_id, season_numbers[0] if season_numbers else 1, episode_number)


def _get_movie_metadata(media_id):
    """Get movie metadata from TMDB."""
    from app.providers import tmdb
    return tmdb.movie(media_id)


def _get_game_metadata(media_id):
    """Get game metadata from IGDB."""
    from app.providers import igdb
    return igdb.game(media_id)


def _get_book_metadata(media_id, source):
    """Get book metadata from appropriate provider."""
    from app.providers import hardcover, openlibrary
    if source == Sources.HARDCOVER.value:
        return hardcover.book(media_id)
    return openlibrary.book(media_id)


def _get_comic_metadata(media_id):
    """Get comic metadata from ComicVine."""
    from app.providers import comicvine
    return comicvine.comic(media_id)


def _get_boardgame_metadata(media_id):
    """Get board game metadata from BGG."""
    from app.providers import bgg
    return bgg.boardgame(media_id)


def _search_anime(query, page):
    """Search for anime on MAL."""
    from app.providers import mal
    return mal.search(MediaTypes.ANIME.value, query, page)


def _search_manga(query, page, source):
    """Search for manga on appropriate provider."""
    from app.providers import mal, mangaupdates
    if source == Sources.MANGAUPDATES.value:
        return mangaupdates.search(query, page)
    return mal.search(MediaTypes.MANGA.value, query, page)


def _search_tv(query, page):
    """Search for TV shows on TMDB."""
    from app.providers import tmdb
    return tmdb.search(MediaTypes.TV.value, query, page)


def _search_movie(query, page):
    """Search for movies on TMDB."""
    from app.providers import tmdb
    return tmdb.search(MediaTypes.MOVIE.value, query, page)


def _search_game(query, page):
    """Search for games on IGDB."""
    from app.providers import igdb
    return igdb.search(query, page)


def _search_book(query, page, source):
    """Search for books on appropriate provider."""
    from app.providers import hardcover, openlibrary
    if source == Sources.HARDCOVER.value:
        return hardcover.search(query, page)
    return openlibrary.search(query, page)


def _search_comic(query, page):
    """Search for comics on ComicVine."""
    from app.providers import comicvine
    return comicvine.search(query, page)


def _search_boardgame(query, page):
    """Search for board games on BGG."""
    from app.providers import bgg
    return bgg.search(query, page)
