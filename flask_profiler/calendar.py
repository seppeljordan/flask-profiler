from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator


class Calendar:
    def day_interval(self, *, since: date, until: date) -> DateSpan:
        return DateSpan(since, until)


@dataclass
class DateSpan:
    since: date
    until: date

    def __contains__(self, element: date) -> bool:
        return self.since <= element and element < self.until

    def __len__(self) -> int:
        return max(0, (self.until - self.since).days)

    def __iter__(self) -> Iterator[date]:
        for i in range((self.until - self.since).days):
            date = self.since + timedelta(days=i)
            yield date
