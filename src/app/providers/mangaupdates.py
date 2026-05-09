"""MangaUpdates provider for manga."""

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

MANGAUPDATES_BASE_URL = 'https://api.mangaupdates.com/v1'


def manga(media_id):
    """Get manga metadata.

    Args:
        media_id: MangaUpdates series ID

    Returns:
        Dict with manga metadata
    """
    url = f'{MANGAUPDATES_BASE_URL}/series/{media_id}'
    data = api_request(Sources.MANGAUPDATES.value, 'GET', url)

    image = data.get('image', {}).get('url', {}).get('original', '')

    return {
        'media_id': str(media_id),
        'title': data.get('title', ''),
        'image': image,
        'media_type': MediaTypes.MANGA.value,
        'source': Sources.MANGAUPDATES.value,
        'max_progress': None,
        'details': {
            'description': data.get('description', ''),
            'year': data.get('year'),
            'status': data.get('status'),
        },
    }


def search(query, page):
    """Search for manga.

    Args:
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    url = f'{MANGAUPDATES_BASE_URL}/series/search'
    limit = 20

    data = api_request(
        Sources.MANGAUPDATES.value,
        'POST',
        url,
        params={
            'search': query,
            'page': page,
            'perpage': limit,
        },
    )

    results = []
    for item in data.get('results', []):
        record = item.get('record', {})
        image = record.get('image', {}).get('url', {}).get('thumb', '')

        results.append({
            'media_id': str(record.get('series_id')),
            'title': record.get('title', ''),
            'image': image,
            'media_type': MediaTypes.MANGA.value,
            'source': Sources.MANGAUPDATES.value,
            'year': str(record.get('year', '')),
        })

    return format_search_response(
        page,
        limit,
        data.get('total_hits', 0),
        results,
    )
