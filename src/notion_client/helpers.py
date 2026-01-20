from typing import Any, Dict


def format_database_title(database: Dict[str, Any]) -> str:
    """
    Extract the title from a database object.

    Args:
        database: Database object from API

    Returns:
        Title string or "Untitled" if not found
    """
    title_array = database.get("title", [])
    if title_array and len(title_array) > 0:
        return " ".join([t["text"]["content"] for t in title_array])
    return "Untitled"


def format_page_title(page: Dict[str, Any]) -> str:
    """
    Extract the title from a page object.

    Args:
        page: Page object from API

    Returns:
        Title string or "Untitled" if not found
    """
    properties = page.get("properties", {})

    # Try to find a title property
    for _prop_name, prop_value in properties.items():
        if prop_value.get("type") == "title":
            title_array = prop_value.get("title", [])
            if title_array and len(title_array) > 0:
                return " ".join([t["text"]["content"] for t in title_array])
    return "Untitled"
