from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Optional


class OptionalStringField:
    def __init__(
        self, name: str, normalize: Callable[[str], str] = lambda x: x
    ) -> None:
        self.name = name
        self.value: Optional[str] = None
        self.normalize = normalize

    def set_field_name(self, name: str) -> None:
        self.name = name

    def parse_value(self, form: Dict[str, str]) -> None:
        raw_value = form.get(self.name) or None
        if raw_value is None:
            self.value = raw_value
        else:
            self.value = self.normalize(raw_value)

    def get_value(self) -> Optional[str]:
        return self.value


class OptionalDatetimeField:
    def __init__(self, name: str) -> None:
        self.name = name
        self.value: Optional[datetime] = None

    def set_field_name(self, name: str) -> None:
        self.name = name

    def parse_value(self, form: Dict[str, str]) -> None:
        raw_value = form.get(self.name) or None
        if raw_value is None:
            return
        try:
            self.value = datetime.fromisoformat(raw_value)
        except ValueError as e:
            raise ValueError(
                f"Cannot parse {raw_value} as datetime object, text is not in ISO format"
            ) from e

    def get_value(self) -> Optional[datetime]:
        return self.value


@dataclass
class FilterFormData:
    name: Optional[str]
    method: Optional[str]
    requested_after: Optional[datetime]
    requested_before: Optional[datetime]
    sorted_by: Optional[str]

    @classmethod
    def parse_from_from(self, args: Dict[str, str]) -> FilterFormData:
        requested_after_field = OptionalDatetimeField(name="requested_after")
        requested_before_field = OptionalDatetimeField(name="requested_before")
        method_field = OptionalStringField(
            name="method",
            normalize=lambda x: x.upper(),
        )
        name_field = OptionalStringField(name="name")
        sorted_by_field = OptionalStringField(name="sorted_by")
        requested_after_field.parse_value(form=args)
        requested_before_field.parse_value(form=args)
        method_field.parse_value(form=args)
        name_field.parse_value(form=args)
        sorted_by_field.parse_value(form=args)
        return FilterFormData(
            method=method_field.get_value(),
            requested_after=requested_after_field.get_value(),
            requested_before=requested_before_field.get_value(),
            name=name_field.get_value(),
            sorted_by=sorted_by_field.get_value(),
        )
