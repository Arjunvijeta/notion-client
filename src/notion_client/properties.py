from typing import Any, Dict, List, Optional


def create_text_property(text: str) -> Dict[str, Any]:
    """
    Create a text property for Notion API.

    Args:
        text: Text content

    Returns:
        Property object
    """
    return {"rich_text": [{"text": {"content": text}}]}


def create_title_property(title: str) -> Dict[str, Any]:
    """
    Create a title property for Notion API.

    Args:
        title: Title text

    Returns:
        Property object
    """
    return {"title": [{"text": {"content": title}}]}


def create_number_property(number: float) -> Dict[str, Any]:
    """
    Create a number property for Notion API.

    Args:
        number: Numeric value

    Returns:
        Property object
    """
    return {"number": number}


def create_checkbox_property(checked: bool) -> Dict[str, Any]:
    """
    Create a checkbox property for Notion API.

    Args:
        checked: Boolean value

    Returns:
        Property object
    """
    return {"checkbox": checked}


def create_select_property(option: str) -> Dict[str, Any]:
    """
    Create a select property for Notion API.

    Args:
        option: Option name

    Returns:
        Property object
    """
    return {"select": {"name": option}}


def create_multi_select_property(options: List[str]) -> Dict[str, Any]:
    """
    Create a multi-select property for Notion API.

    Args:
        options: List of option names

    Returns:
        Property object
    """
    return {"multi_select": [{"name": opt} for opt in options]}


def create_date_property(start_date: str, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a date property for Notion API.

    Args:
        start_date: ISO 8601 date string (e.g., "2026-01-10")
        end_date: Optional end date for date ranges

    Returns:
        Property object
    """
    date_obj = {"start": start_date}
    if end_date:
        date_obj["end"] = end_date
    return {"date": date_obj}


def create_url_property(url: str) -> Dict[str, Any]:
    """
    Create a URL property for Notion API.

    Args:
        url: URL string

    Returns:
        Property object
    """
    return {"url": url}


def create_email_property(email: str) -> Dict[str, Any]:
    """
    Create an email property for Notion API.

    Args:
        email: Email address

    Returns:
        Property object
    """
    return {"email": email}


def create_phone_property(phone: str) -> Dict[str, Any]:
    """
    Create a phone property for Notion API.

    Args:
        phone: Phone number

    Returns:
        Property object
    """
    return {"phone_number": phone}


def create_relation_property(page_ids: List[str]) -> Dict[str, Any]:
    """
    Create a relation property for Notion API.

    Args:
        page_ids: List of related page IDs

    Returns:
        Property object
    """
    return {"relation": [{"id": page_id} for page_id in page_ids]}
