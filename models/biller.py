"""Defines the Biller model for energy consumption billing."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Biller:
    """Represents a billing entity or service provider."""
    id: Optional[int] = None
    name: str = ""
