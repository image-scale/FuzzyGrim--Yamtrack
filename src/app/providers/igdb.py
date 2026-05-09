"""IGDB provider for games."""

from django.conf import settings

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

IGDB_CLIENT_ID = getattr(settings, 'IGDB_CLIENT_ID', '')
IGDB_CLIENT_SECRET = getattr(settings, 'IGDB_CLIENT_SECRET', '')
IGDB_BASE_URL = 'https://api.igdb.com/v4'

_access_token = None


def _get_access_token():
    """Get IGDB access token."""
    global _access_token
    if _access_token:
        return _access_token

    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': IGDB_CLIENT_ID,
        'client_secret': IGDB_CLIENT_SECRET,
        'grant_type': 'client_credentials',
    }
    data = api_request(Sources.IGDB.value, 'POST', url, params=params)
    _access_token = data.get('access_token')
    return _access_token


def _get_headers():
    """Get IGDB API headers."""
    return {
        'Client-ID': IGDB_CLIENT_ID,
        'Authorization': f'Bearer {_get_access_token()}',
    }


def game(media_id):
    """Get game metadata.

    Args:
        media_id: IGDB game ID

    Returns:
        Dict with game metadata
    """
    url = f'{IGDB_BASE_URL}/games'
    body = f'fields name,cover.url,summary,first_release_date; where id = {media_id};'
    data = api_request(
        Sources.IGDB.value,
        'POST',
        url,
        data=body,
        headers=_get_headers(),
    )

    if not data:
        from app.providers.services import raise_not_found_error
        raise_not_found_error(Sources.IGDB.value, media_id, 'game')

    game_data = data[0]
    cover_url = ''
    if game_data.get('cover'):
        cover_url = game_data['cover'].get('url', '').replace('t_thumb', 't_cover_big')
        if cover_url and not cover_url.startswith('http'):
            cover_url = f'https:{cover_url}'

    return {
        'media_id': str(media_id),
        'title': game_data.get('name', ''),
        'image': cover_url,
        'media_type': MediaTypes.GAME.value,
        'source': Sources.IGDB.value,
        'max_progress': None,
        'details': {
            'summary': game_data.get('summary', ''),
            'release_date': game_data.get('first_release_date'),
        },
    }


def search(query, page):
    """Search for games.

    Args:
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    limit = 20
    offset = (page - 1) * limit

    url = f'{IGDB_BASE_URL}/games'
    body = f'search "{query}"; fields name,cover.url,first_release_date; limit {limit}; offset {offset};'
    data = api_request(
        Sources.IGDB.value,
        'POST',
        url,
        data=body,
        headers=_get_headers(),
    )

    results = []
    for item in data or []:
        cover_url = ''
        if item.get('cover'):
            cover_url = item['cover'].get('url', '').replace('t_thumb', 't_cover_big')
            if cover_url and not cover_url.startswith('http'):
                cover_url = f'https:{cover_url}'

        release_date = item.get('first_release_date')
        year = ''
        if release_date:
            from datetime import datetime
            year = str(datetime.fromtimestamp(release_date).year)

        results.append({
            'media_id': str(item.get('id')),
            'title': item.get('name', ''),
            'image': cover_url,
            'media_type': MediaTypes.GAME.value,
            'source': Sources.IGDB.value,
            'year': year,
        })

    return format_search_response(
        page,
        limit,
        len(results) + offset + (limit if len(results) == limit else 0),
        results,
    )
