import re
from dataclasses import dataclass
from datetime import datetime


def act_of(title: str) -> str:
    """The act's name from a show title: before a colon or spaced dash, lower-cased, extra-date labels dropped."""
    first = re.split(r":|\s[-–]\s", title.lower())[0]
    first = re.sub(r"^(second|third|extra|added|new)\s+date\s*", "", first)
    return re.sub(r"[^a-z0-9]+", " ", first).strip()


def uk_now() -> datetime:
    """Current UK clock time (gig times are UK local; the Actions runner is on UTC)."""
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Europe/London")).replace(tzinfo=None)
    except Exception:  # no tz database (e.g. some Windows installs): assume the machine is on UK time
        return datetime.now()


@dataclass
class Event:
    title: str
    start: datetime  # naive local time
    venue: str
    url: str
    source: str
    image: str | None = None
    price: str | None = None
    until: datetime | None = None  # last night, for multi-night runs
    timed: bool = True             # False when the source gave a date but no start time

    def when(self, with_time: bool = True) -> str:
        """Human date text, e.g. "Wed 4 Nov 2026, 19:30" or "Thu 4 - Fri 5 Feb 2027"."""
        day = lambda d, y=True: d.strftime("%a %d %b" + (" %Y" if y else "")).replace(" 0", " ").lstrip("0")
        if self.until:
            return f"{day(self.start, False)} - {day(self.until)}"
        text = day(self.start)
        return f"{text}, {self.start:%H:%M}" if with_time and self.timed else text

    def key(self) -> tuple[str, str, str]:
        """Identity used to merge the same gig seen by different sources."""
        act = act_of(self.title)
        part = "matinee" if self.start.hour < 17 else "evening"
        return (self.start.date().isoformat(), act, part)

    def key_str(self) -> str:
        return "|".join(self.key())
