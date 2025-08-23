"""Business rules and validation logic."""

from typing import List
from .models import User, Item


def validate_user_email(email: str) -> bool:
    """Validate user email format."""
    return "@" in email and "." in email.split("@")[-1]


def get_user_items(user: User, items: List[Item]) -> List[Item]:
    """Get all items owned by a user."""
    return [item for item in items if item.owner_id == user.id]


def can_user_edit_item(user: User, item: Item) -> bool:
    """Check if user can edit an item."""
    return user.active and item.owner_id == user.id