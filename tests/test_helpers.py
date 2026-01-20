"""Tests for helpers module."""

from notion_client import format_database_title, format_page_title


class TestHelpers:
    """Test helper functions."""

    def test_format_database_title_with_title(self):
        """Test formatting database title with valid title."""
        database = {"title": [{"text": {"content": "My Database"}}, {"text": {"content": " Name"}}]}
        # Helper joins with space, so "My Database" + " Name" = "My Database  Name"
        assert format_database_title(database) == "My Database  Name"

    def test_format_database_title_empty(self):
        """Test formatting database title with empty title."""
        database = {"title": []}
        assert format_database_title(database) == "Untitled"

    def test_format_database_title_missing(self):
        """Test formatting database title with missing title."""
        database = {}
        assert format_database_title(database) == "Untitled"

    def test_format_page_title_with_title(self):
        """Test formatting page title with valid title property."""
        page = {
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"text": {"content": "My Page"}}, {"text": {"content": " Title"}}],
                }
            }
        }
        # Helper joins with space, so "My Page" + " Title" = "My Page  Title"
        assert format_page_title(page) == "My Page  Title"

    def test_format_page_title_empty(self):
        """Test formatting page title with empty title."""
        page = {"properties": {"Name": {"type": "title", "title": []}}}
        assert format_page_title(page) == "Untitled"

    def test_format_page_title_missing_properties(self):
        """Test formatting page title with missing properties."""
        page = {}
        assert format_page_title(page) == "Untitled"

    def test_format_page_title_no_title_property(self):
        """Test formatting page title with no title property."""
        page = {"properties": {"Status": {"type": "select", "select": {"name": "Active"}}}}
        assert format_page_title(page) == "Untitled"

    def test_format_page_title_multiple_properties(self):
        """Test that only title property is used."""
        page = {
            "properties": {
                "Status": {"type": "select"},
                "Name": {"type": "title", "title": [{"text": {"content": "Correct Title"}}]},
                "Date": {"type": "date"},
            }
        }
        assert format_page_title(page) == "Correct Title"
