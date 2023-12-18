# This class will be used to store the Availability objects.

import datetime
from dataclasses import dataclass


@dataclass
class AvailabilitySlot:
    starts_at: datetime.date
    ends_at: datetime.date
    unavailable: bool
