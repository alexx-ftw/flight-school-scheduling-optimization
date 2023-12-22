"""
This file contains the class for booking
"""

from dataclasses import dataclass

from classes.aircraft import Aircraft
from classes.flight import Flight
from classes.user import User


@dataclass
class Booking(object):
    """Class for storing booking data"""

    flight: Flight
    aircraft: Aircraft
    instructor: User
    student: User
