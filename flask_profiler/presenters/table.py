from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Table:
    headers: List[Header]
    rows: List[List[Cell]]


@dataclass
class Header:
    label: str
    link_target: Optional[str] = None


@dataclass
class Cell:
    text: str
    link_target: Optional[str] = None
