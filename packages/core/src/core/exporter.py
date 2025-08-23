"""Data export utilities."""

import json
from typing import Any, Dict, List
from .models import User, Item


def export_to_json(data: Any) -> str:
    """Export data to JSON string."""
    if hasattr(data, '__dict__'):
        return json.dumps(data.__dict__, indent=2)
    return json.dumps(data, indent=2)


def export_users_to_dict(users: List[User]) -> List[Dict[str, Any]]:
    """Export users to dictionary format."""
    return [user.__dict__ for user in users]


def export_items_to_dict(items: List[Item]) -> List[Dict[str, Any]]:
    """Export items to dictionary format."""
    return [item.__dict__ for item in items]