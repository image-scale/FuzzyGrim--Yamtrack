"""Hardcover provider for books."""

from django.conf import settings

from app.helpers import format_search_response
from app.models import MediaTypes, Sources
from app.providers.services import api_request

HARDCOVER_API_URL = 'https://api.hardcover.app/v1/graphql'
HARDCOVER_API_KEY = getattr(settings, 'HARDCOVER_API_KEY', '')


def _get_headers():
    """Get Hardcover API headers."""
    return {
        'Authorization': f'Bearer {HARDCOVER_API_KEY}',
        'Content-Type': 'application/json',
    }


def book(media_id):
    """Get book metadata.

    Args:
        media_id: Hardcover book ID

    Returns:
        Dict with book metadata
    """
    query = '''
    query GetBook($id: Int!) {
        books(where: {id: {_eq: $id}}) {
            id
            title
            image
            description
            pages
        }
    }
    '''
    data = api_request(
        Sources.HARDCOVER.value,
        'POST',
        HARDCOVER_API_URL,
        params={'query': query, 'variables': {'id': int(media_id)}},
        headers=_get_headers(),
    )

    books = data.get('data', {}).get('books', [])
    if not books:
        from app.providers.services import raise_not_found_error
        raise_not_found_error(Sources.HARDCOVER.value, media_id, 'book')

    book_data = books[0]
    return {
        'media_id': str(media_id),
        'title': book_data.get('title', ''),
        'image': book_data.get('image', ''),
        'media_type': MediaTypes.BOOK.value,
        'source': Sources.HARDCOVER.value,
        'max_progress': book_data.get('pages'),
        'details': {
            'description': book_data.get('description', ''),
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
    limit = 20
    offset = (page - 1) * limit

    gql_query = '''
    query SearchBooks($query: String!, $limit: Int!, $offset: Int!) {
        books(where: {title: {_ilike: $query}}, limit: $limit, offset: $offset) {
            id
            title
            image
            release_year
        }
    }
    '''
    data = api_request(
        Sources.HARDCOVER.value,
        'POST',
        HARDCOVER_API_URL,
        params={
            'query': gql_query,
            'variables': {'query': f'%{query}%', 'limit': limit, 'offset': offset},
        },
        headers=_get_headers(),
    )

    books = data.get('data', {}).get('books', [])
    results = [
        {
            'media_id': str(book.get('id')),
            'title': book.get('title', ''),
            'image': book.get('image', ''),
            'media_type': MediaTypes.BOOK.value,
            'source': Sources.HARDCOVER.value,
            'year': str(book.get('release_year', '')),
        }
        for book in books
    ]

    return format_search_response(
        page,
        limit,
        len(results) + offset + (limit if len(results) == limit else 0),
        results,
    )
