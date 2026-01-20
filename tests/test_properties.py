"""Tests for properties module."""

from notion_client.properties import (
    create_checkbox_property,
    create_date_property,
    create_email_property,
    create_multi_select_property,
    create_number_property,
    create_phone_property,
    create_relation_property,
    create_select_property,
    create_text_property,
    create_title_property,
    create_url_property,
)


class TestPropertyCreators:
    """Test property creator functions."""

    def test_create_text_property(self):
        """Test creating text property."""
        prop = create_text_property("Hello World")
        assert "rich_text" in prop
        assert len(prop["rich_text"]) == 1
        assert prop["rich_text"][0]["text"]["content"] == "Hello World"

    def test_create_title_property(self):
        """Test creating title property."""
        prop = create_title_property("Page Title")
        assert "title" in prop
        assert len(prop["title"]) == 1
        assert prop["title"][0]["text"]["content"] == "Page Title"

    def test_create_number_property(self):
        """Test creating number property."""
        prop = create_number_property(42)
        assert prop == {"number": 42}

        prop_float = create_number_property(3.14)
        assert prop_float == {"number": 3.14}

    def test_create_checkbox_property(self):
        """Test creating checkbox property."""
        prop_true = create_checkbox_property(True)
        assert prop_true == {"checkbox": True}

        prop_false = create_checkbox_property(False)
        assert prop_false == {"checkbox": False}

    def test_create_select_property(self):
        """Test creating select property."""
        prop = create_select_property("Active")
        assert prop == {"select": {"name": "Active"}}

    def test_create_multi_select_property(self):
        """Test creating multi-select property."""
        prop = create_multi_select_property(["tag1", "tag2", "tag3"])
        assert "multi_select" in prop
        assert len(prop["multi_select"]) == 3
        assert prop["multi_select"][0] == {"name": "tag1"}
        assert prop["multi_select"][1] == {"name": "tag2"}

    def test_create_multi_select_property_empty(self):
        """Test creating multi-select with empty list."""
        prop = create_multi_select_property([])
        assert prop == {"multi_select": []}

    def test_create_date_property_single(self):
        """Test creating date property with single date."""
        prop = create_date_property("2026-01-20")
        assert prop == {"date": {"start": "2026-01-20"}}

    def test_create_date_property_range(self):
        """Test creating date property with date range."""
        prop = create_date_property("2026-01-20", "2026-01-25")
        assert prop["date"]["start"] == "2026-01-20"
        assert prop["date"]["end"] == "2026-01-25"

    def test_create_url_property(self):
        """Test creating URL property."""
        prop = create_url_property("https://example.com")
        assert prop == {"url": "https://example.com"}

    def test_create_email_property(self):
        """Test creating email property."""
        prop = create_email_property("test@example.com")
        assert prop == {"email": "test@example.com"}

    def test_create_phone_property(self):
        """Test creating phone property."""
        prop = create_phone_property("+1234567890")
        assert prop == {"phone_number": "+1234567890"}

    def test_create_relation_property_single(self):
        """Test creating relation property with single page."""
        prop = create_relation_property(["page-id-1"])
        assert prop == {"relation": [{"id": "page-id-1"}]}

    def test_create_relation_property_multiple(self):
        """Test creating relation property with multiple pages."""
        prop = create_relation_property(["page-id-1", "page-id-2", "page-id-3"])
        assert len(prop["relation"]) == 3
        assert prop["relation"][0] == {"id": "page-id-1"}
        assert prop["relation"][1] == {"id": "page-id-2"}

    def test_create_relation_property_empty(self):
        """Test creating relation property with empty list."""
        prop = create_relation_property([])
        assert prop == {"relation": []}
