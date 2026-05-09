"""Export functionality for user media data."""

import csv
import logging

from django.apps import apps
from django.db.models import Field, Prefetch

from app import helpers
from app.models import Episode, Item, MediaTypes, Season

logger = logging.getLogger(__name__)


class Echo:
    """Object implementing write method for streaming CSV output.

    Returns written values directly instead of storing in a buffer,
    enabling streaming responses for large exports.
    """

    def write(self, value):
        """Write the value by returning it."""
        return value


def generate_rows(user):
    """Generate CSV rows for all user media.

    Args:
        user: The user whose media to export

    Yields:
        CSV-formatted rows (header first, then data rows)
    """
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, quoting=csv.QUOTE_ALL)

    fields = {
        'item': get_model_fields(Item),
        'track': get_track_fields(),
    }

    yield writer.writerow(fields['item'] + fields['track'])

    prefetch_config = {
        MediaTypes.TV.value: Prefetch(
            'seasons',
            queryset=Season.objects.select_related('item').prefetch_related(
                Prefetch(
                    'episodes',
                    queryset=Episode.objects.select_related('item'),
                ),
            ),
        ),
        MediaTypes.SEASON.value: Prefetch(
            'episodes',
            queryset=Episode.objects.select_related('item'),
        ),
    }

    for media_type in MediaTypes.values:
        model = apps.get_model('app', media_type)

        filter_kwargs = (
            {'related_season__user': user}
            if media_type == MediaTypes.EPISODE.value
            else {'user': user}
        )

        queryset = model.objects.filter(**filter_kwargs).select_related('item')

        if media_type in prefetch_config:
            queryset = queryset.prefetch_related(prefetch_config[media_type])

        logger.debug('Streaming %ss to CSV', media_type)

        for media in queryset.iterator(chunk_size=500):
            row = [getattr(media.item, field, '') for field in fields['item']] + [
                getattr(media, field, '') for field in fields['track']
            ]

            if media_type == MediaTypes.GAME.value:
                progress_index = fields['track'].index('progress')
                row[progress_index + len(fields['item'])] = helpers.minutes_to_hhmm(
                    media.progress,
                )

            yield writer.writerow(row)

        logger.debug('Finished streaming %ss to CSV', media_type)


def get_model_fields(model):
    """Get list of field names from a model.

    Args:
        model: Django model class

    Returns:
        List of field name strings (excludes auto-created and relation fields)
    """
    return [
        field.name
        for field in model._meta.get_fields()
        if isinstance(field, Field) and not field.auto_created and not field.is_relation
    ]


def get_track_fields():
    """Get list of all track fields from all media models.

    Collects fields from all media types and orders them sensibly,
    putting date fields together and timestamps at the end.

    Returns:
        List of field name strings
    """
    all_fields = []

    for media_type in MediaTypes.values:
        model = apps.get_model('app', media_type)
        for field in get_model_fields(model):
            if field not in all_fields:
                all_fields.append(field)

    if 'start_date' in all_fields and 'end_date' in all_fields:
        end_idx = all_fields.index('end_date')
        all_fields.remove('start_date')
        all_fields.remove('end_date')
        all_fields.insert(end_idx, 'end_date')
        all_fields.insert(end_idx, 'start_date')

    for timestamp_field in ('created_at', 'progressed_at'):
        if timestamp_field in all_fields:
            all_fields.remove(timestamp_field)
            all_fields.append(timestamp_field)

    return list(all_fields)
