from datetime import datetime, timedelta, timezone
from typing import Optional


class FakeClock:
    def __init__(self) -> None:
        self.frozen_time: Optional[datetime] = None

    def freeze_time(self, t: datetime) -> None:
        if t.tzinfo is None:
            t = t.astimezone(timezone.utc)
        self.frozen_time = t

    def unfreeze_time(self) -> None:
        self.frozen_time = None

    def advance_clock(self, dt: timedelta) -> None:
        if self.frozen_time:
            self.frozen_time += dt

    def utc_now(self) -> datetime:
        if self.frozen_time:
            return self.frozen_time
        return datetime.now(tz=timezone.utc)
