"""Tests for the helpers module."""

import pytest

from app.helpers import format_search_response, minutes_to_hhmm


class TestMinutesToHhmm:
    """Tests for minutes_to_hhmm function."""

    def test_zero_minutes(self):
        """Test converting 0 minutes."""
        assert minutes_to_hhmm(0) == '0min'

    def test_minutes_only(self):
        """Test converting minutes less than an hour."""
        assert minutes_to_hhmm(45) == '45min'

    def test_one_hour_exactly(self):
        """Test converting exactly one hour."""
        assert minutes_to_hhmm(60) == '1h 00min'

    def test_one_hour_thirty_minutes(self):
        """Test converting 90 minutes."""
        assert minutes_to_hhmm(90) == '1h 30min'

    def test_two_hours_five_minutes(self):
        """Test converting 125 minutes with leading zero for minutes."""
        assert minutes_to_hhmm(125) == '2h 05min'

    def test_large_value(self):
        """Test converting a large number of minutes."""
        assert minutes_to_hhmm(600) == '10h 00min'

    def test_single_minute(self):
        """Test converting 1 minute."""
        assert minutes_to_hhmm(1) == '1min'

    def test_59_minutes(self):
        """Test converting 59 minutes (just under an hour)."""
        assert minutes_to_hhmm(59) == '59min'


class TestFormatSearchResponse:
    """Tests for format_search_response function."""

    def test_basic_response(self):
        """Test basic search response formatting."""
        results = [{'id': 1, 'title': 'Test'}]
        response = format_search_response(
            page=1,
            per_page=10,
            total_results=1,
            results=results,
        )
        assert response == {
            'page': 1,
            'total_results': 1,
            'total_pages': 1,
            'results': results,
        }

    def test_multiple_pages(self):
        """Test response with multiple pages."""
        results = [{'id': i} for i in range(10)]
        response = format_search_response(
            page=1,
            per_page=10,
            total_results=25,
            results=results,
        )
        assert response['page'] == 1
        assert response['total_results'] == 25
        assert response['total_pages'] == 3
        assert len(response['results']) == 10

    def test_empty_results(self):
        """Test response with no results."""
        response = format_search_response(
            page=1,
            per_page=10,
            total_results=0,
            results=[],
        )
        assert response == {
            'page': 1,
            'total_results': 0,
            'total_pages': 1,
            'results': [],
        }

    def test_second_page(self):
        """Test response for second page."""
        results = [{'id': i} for i in range(10, 20)]
        response = format_search_response(
            page=2,
            per_page=10,
            total_results=25,
            results=results,
        )
        assert response['page'] == 2
        assert response['total_pages'] == 3

    def test_exact_page_boundary(self):
        """Test response when results evenly divide into pages."""
        results = [{'id': i} for i in range(10)]
        response = format_search_response(
            page=1,
            per_page=10,
            total_results=20,
            results=results,
        )
        assert response['total_pages'] == 3

    def test_different_per_page(self):
        """Test response with different per_page value."""
        results = [{'id': i} for i in range(5)]
        response = format_search_response(
            page=1,
            per_page=5,
            total_results=12,
            results=results,
        )
        assert response['total_pages'] == 3
