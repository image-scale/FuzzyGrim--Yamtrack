"""Helper utilities for the app."""


def minutes_to_hhmm(total_minutes):
    """Convert total minutes to human readable format.

    Args:
        total_minutes: Number of minutes to convert

    Returns:
        String in "Xh YYmin" format (e.g., "2h 30min", "45min")
    """
    hours = int(total_minutes / 60)
    minutes = int(total_minutes % 60)
    if hours == 0:
        return f'{minutes}min'
    return f'{hours}h {minutes:02d}min'


def format_search_response(page, per_page, total_results, results):
    """Format the search response for pagination.

    Args:
        page: Current page number
        per_page: Number of results per page
        total_results: Total number of results across all pages
        results: List of result items for the current page

    Returns:
        Dictionary with pagination metadata and results
    """
    return {
        'page': page,
        'total_results': total_results,
        'total_pages': total_results // per_page + 1,
        'results': results,
    }
