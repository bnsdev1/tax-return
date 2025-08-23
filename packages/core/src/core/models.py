"""Shared data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User model."""
    
    id: int
    name: str
    email: str
    active: bool = True


@dataclass
class Item:
    """Item model."""
    
    id: int
    title: str
    description: Optional[str] = None
    owner_id: int