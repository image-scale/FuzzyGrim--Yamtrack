"""History processor for tracking and formatting media changes."""

from django.apps import apps
from django.template.defaultfilters import pluralize

from app import config, helpers
from app.models import MediaTypes, Status
from app.templatetags import app_tags


def process_history_entries(history_records, media_type, media_entry_number, user):
    """Process all history records into timeline entries.

    Args:
        history_records: QuerySet of historical records
        media_type: The media type value
        media_entry_number: The entry number for the media
        user: The user for date formatting

    Returns:
        List of timeline entry dictionaries
    """
    timeline_entries = []
    last = history_records.first()

    for _ in range(history_records.count()):
        entry = process_history_entry((last, last.prev_record), media_type, user)
        if entry['changes']:
            entry['media_entry_number'] = media_entry_number
            timeline_entries.append(entry)
        last = last.prev_record

    return timeline_entries


def process_history_entry(entry, media_type, user):
    """Process a single history entry to organize and format changes.

    Args:
        entry: Tuple of (new_record, old_record)
        media_type: The media type value
        user: The user for date formatting

    Returns:
        Dictionary with id, date, and changes list
    """
    new_record, old_record = entry
    processed_entry = {
        'id': new_record.history_id,
        'date': new_record.history_date,
        'changes': [],
    }

    if old_record is not None:
        return process_changed_entry(
            new_record,
            old_record,
            media_type,
            processed_entry,
            user,
        )
    return process_creation_entry(new_record, media_type, processed_entry, user)


def process_changed_entry(new_record, old_record, media_type, processed_entry, user):
    """Process an entry representing a change to existing media.

    Args:
        new_record: The new historical record
        old_record: The previous historical record
        media_type: The media type value
        processed_entry: The entry dict to populate
        user: The user for date formatting

    Returns:
        The populated processed_entry dictionary
    """
    delta = new_record.diff_against(old_record)
    changes = organize_changes(delta.changes, media_type, user)
    apply_date_status_integration(changes, user)
    build_changes_list(changes, processed_entry)
    return processed_entry


def process_creation_entry(new_record, media_type, processed_entry, user):
    """Process an entry representing media creation.

    Args:
        new_record: The historical record for the creation
        media_type: The media type value
        processed_entry: The entry dict to populate
        user: The user for date formatting

    Returns:
        The populated processed_entry dictionary
    """
    history_model = apps.get_model(
        app_label='app',
        model_name=f'historical{media_type}',
    )

    changes = collect_creation_changes(new_record, history_model, media_type, user)
    apply_date_status_integration(changes, user)
    build_changes_list(changes, processed_entry)
    return processed_entry


def organize_changes(changes, media_type, user):
    """Organize changes into categories.

    Args:
        changes: List of change objects from diff_against
        media_type: The media type value
        user: The user for date formatting

    Returns:
        Dictionary with date_changes, status_change, and other_changes
    """
    organized = {
        'date_changes': {'start_date': None, 'end_date': None},
        'status_change': None,
        'other_changes': [],
    }

    end_date_change = None

    for change in changes:
        if change.field == 'progress' and media_type == MediaTypes.MOVIE.value:
            continue

        change_data = {
            'description': format_description(
                change.field,
                change.old,
                change.new,
                media_type,
                user,
            ),
            'field': change.field,
            'old': change.old,
            'new': change.new,
        }

        if change.field == 'status':
            organized['status_change'] = change_data
        elif change.field == 'end_date':
            end_date_change = change_data
        elif change.field in organized['date_changes']:
            organized['date_changes'][change.field] = change_data
        else:
            organized['other_changes'].append(change_data)

    if end_date_change:
        organized['date_changes']['end_date'] = end_date_change

    return organized


def collect_creation_changes(new_record, history_model, media_type, user):
    """Collect changes for a creation entry.

    Args:
        new_record: The historical record for the creation
        history_model: The historical model class
        media_type: The media type value
        user: The user for date formatting

    Returns:
        Dictionary with date_changes, status_change, and other_changes
    """
    organized = {
        'date_changes': {'start_date': None, 'end_date': None},
        'status_change': None,
        'other_changes': [],
    }

    for field in history_model._meta.get_fields():
        if (
            field.name.startswith('history_')
            or field.name == 'id'
            or not hasattr(new_record, field.attname)
            or (field.name == 'progress' and media_type == MediaTypes.MOVIE.value)
        ):
            continue

        value = getattr(new_record, field.attname, None)
        if not value and not (
            media_type == MediaTypes.EPISODE.value and field.name == 'end_date'
        ):
            continue

        change_data = {
            'field': field.name,
            'new': value,
            'description': format_description(
                field.name,
                None,
                value,
                media_type,
                user,
            ),
        }

        if field.name == 'status':
            organized['status_change'] = change_data
        elif field.name in organized['date_changes']:
            organized['date_changes'][field.name] = change_data
        elif field.name not in ['item', 'user', 'related_tv']:
            organized['other_changes'].append(change_data)

    return organized


def apply_date_status_integration(changes, user):
    """Integrate status changes with date changes where appropriate.

    Args:
        changes: The organized changes dictionary
        user: The user for date formatting
    """
    date_changes = changes['date_changes']
    status_change = changes['status_change']

    if (
        date_changes['start_date']
        and status_change
        and status_change['new'] == Status.IN_PROGRESS.value
    ):
        date_changes['start_date']['description'] = (
            f"Started on "
            f"{app_tags.datetime_format(date_changes['start_date']['new'], user)}"
        )
        changes['status_change'] = None

    if (
        date_changes['end_date']
        and status_change
        and status_change['new'] == Status.COMPLETED.value
    ):
        date_changes['end_date']['description'] = (
            f"Finished on "
            f"{app_tags.datetime_format(date_changes['end_date']['new'], user)}"
        )
        changes['status_change'] = None


def build_changes_list(changes, processed_entry):
    """Build the final changes list in the desired order.

    Args:
        changes: The organized changes dictionary
        processed_entry: The entry dict to populate with changes
    """
    if changes['date_changes']['start_date']:
        processed_entry['changes'].append(changes['date_changes']['start_date'])
    if changes['date_changes']['end_date']:
        processed_entry['changes'].append(changes['date_changes']['end_date'])

    if changes['status_change']:
        processed_entry['changes'].append(changes['status_change'])

    processed_entry['changes'].extend(changes['other_changes'])


def format_description(field_name, old_value, new_value, media_type=None, user=None):
    """Format change description in a human-readable way.

    Args:
        field_name: The name of the field that changed
        old_value: The previous value (None for creation)
        new_value: The new value
        media_type: The media type value
        user: The user for date formatting

    Returns:
        Human-readable description string
    """
    if field_name in {'start_date', 'end_date'}:
        new_value = app_tags.datetime_format(new_value, user)
        old_value = app_tags.datetime_format(old_value, user)

    if old_value is None:
        if field_name == 'status':
            verb = config.get_verb(media_type, past_tense=False)
            action = 'Marked as'
            if new_value == Status.IN_PROGRESS.value:
                return f'{action} currently {verb}ing'
            if new_value == Status.COMPLETED.value:
                return f'{action} finished {verb}ing'
            if new_value == Status.PLANNING.value:
                return f'Added to {verb}ing list'
            if new_value == Status.DROPPED.value:
                return f'{action} dropped'
            if new_value == Status.PAUSED.value:
                return f'{action} paused {verb}ing'

        if field_name == 'score':
            return f'Rated {new_value}/10'

        if field_name == 'progress' and media_type:
            verb = config.get_verb(media_type, past_tense=True).title()
            if media_type == MediaTypes.GAME.value:
                return f'{verb} for {helpers.minutes_to_hhmm(new_value)}'
            unit = config.get_unit(media_type, short=False)
            if unit:
                return f'{verb} up to {unit.lower()} {new_value}'
            return f'{verb} up to {new_value}'

        if field_name in ['start_date', 'end_date']:
            field_display = 'Started' if field_name == 'start_date' else 'Finished'
            if new_value:
                return f'{field_display} on {new_value}'
            return f'{field_display} without date'

        if field_name == 'notes':
            return 'Added notes'

        return f"Set {field_name.replace('_', ' ').lower()} to {new_value}"

    if field_name == 'status':
        verb = config.get_verb(media_type, past_tense=False)
        transitions = {
            (
                Status.PLANNING.value,
                Status.IN_PROGRESS.value,
            ): f'Currently {verb}ing',
            (
                Status.IN_PROGRESS.value,
                Status.COMPLETED.value,
            ): f'Finished {verb}ing',
            (
                Status.IN_PROGRESS.value,
                Status.PAUSED.value,
            ): f'Paused {verb}ing',
            (
                Status.PAUSED.value,
                Status.IN_PROGRESS.value,
            ): f'Resumed {verb}ing',
            (
                Status.IN_PROGRESS.value,
                Status.DROPPED.value,
            ): f'Stopped {verb}ing',
        }
        return transitions.get(
            (old_value, new_value),
            f'Changed status from {old_value} to {new_value}',
        )

    if field_name == 'score':
        if old_value == 0:
            return f'Rated {new_value}/10'
        return f'Changed rating from {old_value} to {new_value}'

    if field_name == 'progress':
        diff = new_value - old_value
        diff_abs = abs(diff)

        if media_type == MediaTypes.GAME.value:
            if diff > 0:
                return f'Added {helpers.minutes_to_hhmm(diff_abs)} of playtime'
            return f'Removed {helpers.minutes_to_hhmm(diff_abs)} of playtime'

        unit = config.get_unit(media_type, short=False)
        if unit:
            unit_str = f'{unit.lower()}{pluralize(new_value)}'
            return f'Progress set to {new_value} {unit_str}'
        return f'Progress set to {new_value}'

    if field_name in ['start_date', 'end_date']:
        field_display = 'Start' if field_name == 'start_date' else 'End'
        if not new_value:
            return f'Removed {field_display.lower()} date'
        if not old_value:
            return f'{field_display}ed on {new_value}'
        return f'{field_display} date changed to {new_value}'

    if field_name == 'notes':
        if not old_value:
            return 'Added notes'
        if not new_value:
            return 'Removed notes'
        return 'Updated notes'

    field_label = field_name.replace('_', ' ').lower()
    return f'Updated {field_label} from {old_value} to {new_value}'
