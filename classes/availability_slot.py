"""
AvailabilitySlot class
"""

import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class AvailabilitySlot(object):
    """
    This class will be used to store the AvailabilitySlot objects.
    """

    starts_at: datetime.date
    ends_at: datetime.date
    unavailable: Optional[bool] = None
