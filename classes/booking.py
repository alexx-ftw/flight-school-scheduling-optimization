"""
This file contains the class for booking
"""

import datetime
from dataclasses import dataclass

from classes.aircraft import Aircraft
from classes.flight import Flight


@dataclass
class Booking(object):
    """Class for storing booking data"""

    briefing_time: datetime.datetime
    flight: Flight
    aircraft: Aircraft
    debriefing_time: datetime.datetime

    # instructor: User
    # student: User
