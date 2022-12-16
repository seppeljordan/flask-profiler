from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class FakeJsonRequest:
    data: Optional[Any] = None

    def get_content_as_json(self) -> Optional[str]:
        return self.data
