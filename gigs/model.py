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

    def key(self) -> tuple[str, str, str]:
        """Identity used to merge the same gig seen by different sources."""
        act = re.sub(r"[^a-z0-9]+", " ", self.title.lower().split(":")[0]).strip()
        part = "matinee" if self.start.hour < 17 else "evening"
        return (self.start.date().isoformat(), act, part)
