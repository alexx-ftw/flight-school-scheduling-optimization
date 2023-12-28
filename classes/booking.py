"""
This file contains the class for booking
"""

import datetime
from dataclasses import dataclass


@dataclass
class Booking(object):
    """Class for storing booking data"""

    starts_at: datetime.datetime
    from classes.flight import Flight

    flight_data: Flight
    ends_at: datetime.datetime
    comment: str
    id: str
    status: str
    from classes.user import User

    instructor: User
    student: User
