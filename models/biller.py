"""Defines the Biller model for energy consumption billing."""
from dataclasses import dataclass
from typing import Optional

@dataclass(kw_only=True)
class Biller:
    """Represents a billing entity or service provider."""
    id: int | None = None
    name: str
    website: str | None = None
