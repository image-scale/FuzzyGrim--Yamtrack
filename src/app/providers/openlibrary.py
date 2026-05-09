"""OpenLibrary provider for books."""

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

OPENLIBRARY_BASE_URL = 'https://openlibrary.org'
OPENLIBRARY_COVERS_URL = 'https://covers.openlibrary.org'


def book(media_id):
    """Get book metadata.

    Args:
        media_id: OpenLibrary work ID

    Returns:
        Dict with book metadata
    """
    url = f'{OPENLIBRARY_BASE_URL}/works/{media_id}.json'
    data = api_request(Sources.OPENLIBRARY.value, 'GET', url)

    cover_id = data.get('covers', [None])[0]
    image = ''
    if cover_id:
        image = f'{OPENLIBRARY_COVERS_URL}/b/id/{cover_id}-L.jpg'

    return {
        'media_id': media_id,
        'title': data.get('title', ''),
        'image': image,
        'media_type': MediaTypes.BOOK.value,
        'source': Sources.OPENLIBRARY.value,
        'max_progress': None,
        'details': {
            'description': data.get('description', {}).get('value', '') if isinstance(data.get('description'), dict) else data.get('description', ''),
        },
    }


def search(query, page):
    """Search for books.

    Args:
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    url = f'{OPENLIBRARY_BASE_URL}/search.json'
    params = {
        'q': query,
        'page': page,
        'limit': 20,
    }
    data = api_request(Sources.OPENLIBRARY.value, 'GET', url, params=params)

    results = []
    for item in data.get('docs', []):
        key = item.get('key', '')
        media_id = key.replace('/works/', '') if key else ''
        cover_id = item.get('cover_i')
        image = f'{OPENLIBRARY_COVERS_URL}/b/id/{cover_id}-M.jpg' if cover_id else ''

        results.append({
            'media_id': media_id,
            'title': item.get('title', ''),
            'image': image,
            'media_type': MediaTypes.BOOK.value,
            'source': Sources.OPENLIBRARY.value,
            'year': str(item.get('first_publish_year', '')),
        })

    return format_search_response(
        page,
        20,
        data.get('numFound', 0),
        results,
    )
