"""Media type and status configuration for the app."""

from app.models import MediaTypes, Status


MEDIA_TYPE_CONFIG = {
    MediaTypes.TV.value: {
        'verb': ('watch', 'watched'),
        'unit': None,
    },
    MediaTypes.SEASON.value: {
        'verb': ('watch', 'watched'),
        'unit': ('E', 'Episode'),
    },
    MediaTypes.EPISODE.value: {
        'verb': ('watch', 'watched'),
        'unit': None,
    },
    MediaTypes.MOVIE.value: {
        'verb': ('watch', 'watched'),
        'unit': None,
    },
    MediaTypes.ANIME.value: {
        'verb': ('watch', 'watched'),
        'unit': ('E', 'Episode'),
    },
    MediaTypes.MANGA.value: {
        'verb': ('read', 'read'),
        'unit': ('#', 'Chapter'),
    },
    MediaTypes.GAME.value: {
        'verb': ('play', 'played'),
        'unit': None,
    },
    MediaTypes.BOOK.value: {
        'verb': ('read', 'read'),
        'unit': ('P', 'Page'),
    },
    MediaTypes.COMIC.value: {
        'verb': ('read', 'read'),
        'unit': ('#', 'Issue'),
    },
    MediaTypes.BOARDGAME.value: {
        'verb': ('play', 'played'),
        'unit': ('#', 'Play'),
    },
}


STATUS_CONFIG = {
    Status.COMPLETED.value: {
        'text_color': 'text-emerald-400',
        'hex': '#10b981',
    },
    Status.IN_PROGRESS.value: {
        'text_color': 'text-indigo-400',
        'hex': '#6366f1',
    },
    Status.PAUSED.value: {
        'text_color': 'text-orange-400',
        'hex': '#f97316',
    },
    Status.PLANNING.value: {
        'text_color': 'text-sky-400',
        'hex': '#87ceeb',
    },
    Status.DROPPED.value: {
        'text_color': 'text-red-400',
        'hex': '#ef4444',
    },
}


def get_property(media_type, prop_name):
    """Get a property for a media type."""
    config = MEDIA_TYPE_CONFIG.get(media_type)
    if config is None:
        msg = f"Media type '{media_type}' not found in configuration."
        raise KeyError(msg)
    try:
        return config[prop_name]
    except KeyError:
        msg = f"Property '{prop_name}' not found for media type '{media_type}'."
        raise KeyError(msg) from None


def get_verb(media_type, past_tense):
    """Get the verb (present or past tense) for a media type.

    Args:
        media_type: The media type value
        past_tense: If True, return past tense verb

    Returns:
        The verb string
    """
    verbs = get_property(media_type, 'verb')
    return verbs[1] if past_tense else verbs[0]


def get_unit(media_type, short):
    """Get the unit of measurement for a media type.

    Args:
        media_type: The media type value
        short: If True, return short form (e.g., 'E'), else long form (e.g., 'Episode')

    Returns:
        The unit string or None if not applicable
    """
    unit = get_property(media_type, 'unit')
    if unit is None:
        return None
    return unit[0] if short else unit[1]


def get_status_property(status, prop_name):
    """Get a property for a status."""
    config = STATUS_CONFIG.get(status)
    if config is None:
        msg = f"Status '{status}' not found in configuration."
        raise KeyError(msg)
    try:
        return config[prop_name]
    except KeyError:
        msg = f"Property '{prop_name}' not found for status '{status}'."
        raise KeyError(msg) from None
