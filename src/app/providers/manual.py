"""Manual provider for user-created media entries."""

from django.conf import settings

from app.helpers import format_search_response

DEFAULT_IMAGE = getattr(settings, 'IMG_NONE', '')


def metadata(media_id, media_type):
    """Get metadata for a manual entry.

    Args:
        media_id: The ID of the manual entry
        media_type: The type of media

    Returns:
        Dict with basic metadata structure
    """
    return {
        'media_id': media_id,
        'media_type': media_type,
        'title': f'Manual Entry {media_id}',
        'image': DEFAULT_IMAGE,
        'max_progress': None,
        'details': {},
        'related': {},
    }


def season(media_id, season_number):
    """Get metadata for a manual season.

    Args:
        media_id: The ID of the manual entry
        season_number: The season number

    Returns:
        Dict with season metadata
    """
    return {
        'media_id': media_id,
        'season_number': season_number,
        'title': f'Manual Entry {media_id}',
        'image': DEFAULT_IMAGE,
        'episodes': [],
    }


def episode(media_id, season_number, episode_number):
    """Get metadata for a manual episode.

    Args:
        media_id: The ID of the manual entry
        season_number: The season number
        episode_number: The episode number

    Returns:
        Dict with episode metadata
    """
    return {
        'media_id': media_id,
        'season_number': season_number,
        'episode_number': episode_number,
        'title': f'Manual Entry {media_id} S{season_number}E{episode_number}',
        'image': DEFAULT_IMAGE,
    }


def search(query, page):
    """Search is not supported for manual entries.

    Args:
        query: The search query
        page: The page number

    Returns:
        Empty search response
    """
    return format_search_response(page, 20, 0, [])
