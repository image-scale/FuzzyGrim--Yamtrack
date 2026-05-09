"""TMDB provider for TV shows and movies."""

from django.conf import settings

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

TMDB_API_KEY = getattr(settings, 'TMDB_API_KEY', '')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/original'


def _get_headers():
    """Get TMDB API headers."""
    return {
        'Authorization': f'Bearer {TMDB_API_KEY}',
        'Content-Type': 'application/json',
    }


def _format_image(path):
    """Format TMDB image path to full URL."""
    if path:
        return f'{TMDB_IMAGE_BASE}{path}'
    return ''


def tv(media_id):
    """Get TV show metadata.

    Args:
        media_id: TMDB TV show ID

    Returns:
        Dict with TV show metadata
    """
    url = f'{TMDB_BASE_URL}/tv/{media_id}'
    data = api_request(
        Sources.TMDB.value,
        'GET',
        url,
        headers=_get_headers(),
    )

    return {
        'media_id': str(media_id),
        'title': data.get('name', ''),
        'image': _format_image(data.get('poster_path')),
        'media_type': MediaTypes.TV.value,
        'source': Sources.TMDB.value,
        'max_progress': data.get('number_of_episodes'),
        'details': {
            'overview': data.get('overview', ''),
            'first_air_date': data.get('first_air_date'),
            'status': data.get('status'),
            'seasons': data.get('number_of_seasons', 0),
        },
        'related': {
            'seasons': [
                {
                    'season_number': s.get('season_number'),
                    'image': _format_image(s.get('poster_path')),
                    'episode_count': s.get('episode_count', 0),
                }
                for s in data.get('seasons', [])
            ],
        },
    }


def tv_with_seasons(media_id, season_numbers):
    """Get TV show with season details.

    Args:
        media_id: TMDB TV show ID
        season_numbers: List of season numbers to fetch

    Returns:
        Dict with TV and season metadata
    """
    result = tv(media_id)

    for season_num in season_numbers or []:
        url = f'{TMDB_BASE_URL}/tv/{media_id}/season/{season_num}'
        season_data = api_request(
            Sources.TMDB.value,
            'GET',
            url,
            headers=_get_headers(),
        )

        result[f'season/{season_num}'] = {
            'season_number': season_num,
            'title': result['title'],
            'image': _format_image(season_data.get('poster_path')),
            'episodes': [
                {
                    'episode_number': ep.get('episode_number'),
                    'name': ep.get('name', ''),
                    'air_date': ep.get('air_date'),
                    'still_path': ep.get('still_path'),
                }
                for ep in season_data.get('episodes', [])
            ],
        }

    return result


def episode(media_id, season_number, episode_number):
    """Get episode metadata.

    Args:
        media_id: TMDB TV show ID
        season_number: Season number
        episode_number: Episode number

    Returns:
        Dict with episode metadata
    """
    url = f'{TMDB_BASE_URL}/tv/{media_id}/season/{season_number}/episode/{episode_number}'
    data = api_request(
        Sources.TMDB.value,
        'GET',
        url,
        headers=_get_headers(),
    )

    return {
        'media_id': str(media_id),
        'season_number': season_number,
        'episode_number': episode_number,
        'title': data.get('name', ''),
        'image': _format_image(data.get('still_path')),
        'air_date': data.get('air_date'),
    }


def movie(media_id):
    """Get movie metadata.

    Args:
        media_id: TMDB movie ID

    Returns:
        Dict with movie metadata
    """
    url = f'{TMDB_BASE_URL}/movie/{media_id}'
    data = api_request(
        Sources.TMDB.value,
        'GET',
        url,
        headers=_get_headers(),
    )

    return {
        'media_id': str(media_id),
        'title': data.get('title', ''),
        'image': _format_image(data.get('poster_path')),
        'media_type': MediaTypes.MOVIE.value,
        'source': Sources.TMDB.value,
        'max_progress': 1,
        'details': {
            'overview': data.get('overview', ''),
            'release_date': data.get('release_date'),
            'runtime': data.get('runtime'),
        },
    }


def search(media_type, query, page):
    """Search for TV shows or movies.

    Args:
        media_type: 'tv' or 'movie'
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    endpoint = 'tv' if media_type == MediaTypes.TV.value else 'movie'
    url = f'{TMDB_BASE_URL}/search/{endpoint}'
    data = api_request(
        Sources.TMDB.value,
        'GET',
        url,
        params={'query': query, 'page': page},
        headers=_get_headers(),
    )

    results = []
    for item in data.get('results', []):
        title = item.get('name') if endpoint == 'tv' else item.get('title')
        results.append({
            'media_id': str(item.get('id')),
            'title': title or '',
            'image': _format_image(item.get('poster_path')),
            'media_type': media_type,
            'source': Sources.TMDB.value,
            'year': (item.get('first_air_date') or item.get('release_date') or '')[:4],
        })

    return format_search_response(
        page,
        20,
        data.get('total_results', 0),
        results,
    )
