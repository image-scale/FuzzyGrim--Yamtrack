"""BoardGameGeek provider for board games."""

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

BGG_BASE_URL = 'https://boardgamegeek.com/xmlapi2'


def boardgame(media_id):
    """Get board game metadata.

    Args:
        media_id: BGG game ID

    Returns:
        Dict with board game metadata
    """
    url = f'{BGG_BASE_URL}/thing'
    params = {
        'id': media_id,
        'stats': 1,
    }
    root = api_request(
        Sources.BGG.value,
        'GET',
        url,
        params=params,
        response_format='xml',
    )

    item = root.find('item')
    if item is None:
        from app.providers.services import raise_not_found_error
        raise_not_found_error(Sources.BGG.value, media_id, 'boardgame')

    name_elem = item.find("name[@type='primary']")
    title = name_elem.get('value', '') if name_elem is not None else ''

    image_elem = item.find('image')
    image = image_elem.text if image_elem is not None else ''

    description_elem = item.find('description')
    description = description_elem.text if description_elem is not None else ''

    return {
        'media_id': str(media_id),
        'title': title,
        'image': image,
        'media_type': MediaTypes.BOARDGAME.value,
        'source': Sources.BGG.value,
        'max_progress': None,
        'details': {
            'description': description,
        },
    }


def search(query, page):
    """Search for board games.

    Args:
        query: Search query
        page: Page number

    Returns:
        Formatted search response
    """
    url = f'{BGG_BASE_URL}/search'
    params = {
        'query': query,
        'type': 'boardgame',
    }
    root = api_request(
        Sources.BGG.value,
        'GET',
        url,
        params=params,
        response_format='xml',
    )

    all_items = root.findall('item')
    limit = 20
    offset = (page - 1) * limit
    items = all_items[offset:offset + limit]

    results = []
    for item in items:
        name_elem = item.find("name[@type='primary']")
        if name_elem is None:
            name_elem = item.find('name')
        title = name_elem.get('value', '') if name_elem is not None else ''

        yearpublished = item.find('yearpublished')
        year = yearpublished.get('value', '') if yearpublished is not None else ''

        results.append({
            'media_id': item.get('id', ''),
            'title': title,
            'image': '',
            'media_type': MediaTypes.BOARDGAME.value,
            'source': Sources.BGG.value,
            'year': year,
        })

    return format_search_response(
        page,
        limit,
        len(all_items),
        results,
    )
