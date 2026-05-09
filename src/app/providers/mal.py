"""MyAnimeList provider for anime and manga."""

from django.conf import settings

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

MAL_CLIENT_ID = getattr(settings, 'MAL_CLIENT_ID', '')
MAL_BASE_URL = 'https://api.myanimelist.net/v2'


def _get_headers():
    """Get MAL API headers."""
    return {
        'X-MAL-CLIENT-ID': MAL_CLIENT_ID,
    }


def _format_image(images):
    """Extract image URL from MAL image structure."""
    if images and 'large' in images:
        return images['large']
    if images and 'medium' in images:
        return images['medium']
    return ''


def anime(media_id):
    """Get anime metadata.

    Args:
        media_id: MAL anime ID

    Returns:
        Dict with anime metadata
    """
    url = f'{MAL_BASE_URL}/anime/{media_id}'
    params = {
        'fields': 'title,main_picture,synopsis,num_episodes,status,start_date,end_date',
    }
    data = api_request(
        Sources.MAL.value,
        'GET',
        url,
        params=params,
        headers=_get_headers(),
    )

    return {
        'media_id': str(media_id),
        'title': data.get('title', ''),
        'image': _format_image(data.get('main_picture')),
        'media_type': MediaTypes.ANIME.value,
        'source': Sources.MAL.value,
        'max_progress': data.get('num_episodes'),
        'details': {
            'synopsis': data.get('synopsis', ''),
            'status': data.get('status'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
        },
    }


def manga(media_id):
    """Get manga metadata.

    Args:
        media_id: MAL manga ID

    Returns:
        Dict with manga metadata
    """
    url = f'{MAL_BASE_URL}/manga/{media_id}'
    params = {
        'fields': 'title,main_picture,synopsis,num_chapters,num_volumes,status,start_date,end_date',
    }
    data = api_request(
        Sources.MAL.value,
        'GET',
        url,
        params=params,
        headers=_get_headers(),
    )

    return {
        'media_id': str(media_id),
        'title': data.get('title', ''),
        'image': _format_image(data.get('main_picture')),
        'media_type': MediaTypes.MANGA.value,
        'source': Sources.MAL.value,
        'max_progress': data.get('num_chapters'),
        'details': {
            'synopsis': data.get('synopsis', ''),
            'status': data.get('status'),
            'volumes': data.get('num_volumes'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
        },
    }


def search(media_type, query, page):
    """Search for anime or manga.

    Args:
        media_type: 'anime' or 'manga'
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    endpoint = 'anime' if media_type == MediaTypes.ANIME.value else 'manga'
    url = f'{MAL_BASE_URL}/{endpoint}'
    limit = 20
    offset = (page - 1) * limit

    params = {
        'q': query,
        'limit': limit,
        'offset': offset,
        'fields': 'main_picture,start_date',
    }
    data = api_request(
        Sources.MAL.value,
        'GET',
        url,
        params=params,
        headers=_get_headers(),
    )

    results = []
    for item in data.get('data', []):
        node = item.get('node', {})
        results.append({
            'media_id': str(node.get('id')),
            'title': node.get('title', ''),
            'image': _format_image(node.get('main_picture')),
            'media_type': media_type,
            'source': Sources.MAL.value,
            'year': (node.get('start_date') or '')[:4],
        })

    paging = data.get('paging', {})
    has_next = 'next' in paging
    total_estimate = offset + len(results) + (limit if has_next else 0)

    return format_search_response(
        page,
        limit,
        total_estimate,
        results,
    )
