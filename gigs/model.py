import re
from dataclasses import dataclass
from datetime import datetime


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

    def when(self, with_time: bool = True) -> str:
        """Human date text, e.g. "Wed 4 Nov 2026, 19:30" or "Thu 4 - Fri 5 Feb 2027"."""
        day = lambda d, y=True: d.strftime("%a %d %b" + (" %Y" if y else "")).replace(" 0", " ").lstrip("0")
        if self.until:
            return f"{day(self.start, False)} - {day(self.until)}"
        text = day(self.start)
        return f"{text}, {self.start:%H:%M}" if with_time else text

    def key(self) -> tuple[str, str, str]:
        """Identity used to merge the same gig seen by different sources."""
        act = re.sub(r"[^a-z0-9]+", " ", re.split(r":|\s[-–]\s", self.title.lower())[0]).strip()
        part = "matinee" if self.start.hour < 17 else "evening"
        return (self.start.date().isoformat(), act, part)

    def key_str(self) -> str:
        return "|".join(self.key())
