"""Template tags for the app."""

from django import template
from django.utils import formats, timezone

register = template.Library()


@register.filter
def datetime_format(dt, user=None):
    """Format a datetime using user's preferred formats.

    Args:
        dt: The datetime object to format
        user: Optional user object for date format preferences

    Returns:
        Formatted date string or None
    """
    if not dt:
        return None

    if timezone.is_aware(dt):
        local_dt = timezone.localtime(dt)
    else:
        local_dt = dt

    date_format = getattr(user, 'date_format', 'N j, Y') if user else 'N j, Y'
    return formats.date_format(local_dt, date_format)
