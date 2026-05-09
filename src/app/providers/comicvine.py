"""ComicVine provider for comics."""

from django.conf import settings

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

COMICVINE_API_KEY = getattr(settings, 'COMICVINE_API_KEY', '')
COMICVINE_BASE_URL = 'https://comicvine.gamespot.com/api'


def _get_params():
    """Get base ComicVine API params."""
    return {
        'api_key': COMICVINE_API_KEY,
        'format': 'json',
    }


def comic(media_id):
    """Get comic metadata.

    Args:
        media_id: ComicVine volume ID

    Returns:
        Dict with comic metadata
    """
    url = f'{COMICVINE_BASE_URL}/volume/4050-{media_id}/'
    params = _get_params()
    params['field_list'] = 'id,name,image,description,count_of_issues'

    data = api_request(Sources.COMICVINE.value, 'GET', url, params=params)

    if data.get('error') != 'OK':
        from app.providers.services import raise_not_found_error
        raise_not_found_error(Sources.COMICVINE.value, media_id, 'comic')

    result = data.get('results', {})
    return {
        'media_id': str(media_id),
        'title': result.get('name', ''),
        'image': result.get('image', {}).get('original_url', ''),
        'media_type': MediaTypes.COMIC.value,
        'source': Sources.COMICVINE.value,
        'max_progress': result.get('count_of_issues'),
        'details': {
            'description': result.get('description', ''),
        },
    }


def search(query, page):
    """Search for comics.

    Args:
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    limit = 20
    offset = (page - 1) * limit

    url = f'{COMICVINE_BASE_URL}/search/'
    params = _get_params()
    params.update({
        'query': query,
        'resources': 'volume',
        'field_list': 'id,name,image,start_year',
        'limit': limit,
        'offset': offset,
    })

    data = api_request(Sources.COMICVINE.value, 'GET', url, params=params)

    results = []
    for item in data.get('results', []):
        results.append({
            'media_id': str(item.get('id')),
            'title': item.get('name', ''),
            'image': item.get('image', {}).get('original_url', ''),
            'media_type': MediaTypes.COMIC.value,
            'source': Sources.COMICVINE.value,
            'year': str(item.get('start_year', '')),
        })

    return format_search_response(
        page,
        limit,
        data.get('number_of_total_results', 0),
        results,
    )
