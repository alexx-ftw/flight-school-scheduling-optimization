"""
This file contains the class for booking
"""

import datetime
from typing import Any

from classes.aircraft import Aircraft
from classes.flight import Flight
from classes.user import User


class Booking(object):
    """Class for storing booking data"""

    def __init__(
        self,
        starts_at: datetime.datetime,
        flight: Flight,
        ends_at: datetime.datetime,
        comment: str,
        id: str,
        status: str,
        instructor: User,
        student: User,
        planned_lesson: dict[str, Any] | None,
        aircraft: Aircraft,
    ) -> None:
        self.starts_at = starts_at
        self.flight = flight
        self.ends_at = ends_at
        self.comment = comment
        self.id = id
        self.status = status
        self.instructor = instructor
        self.student = student
        self.planned_lesson = planned_lesson
        self.aircraft = aircraft

        self.aircraft.bookings.append(self)

        self.aircraft.sch_date_booked_flight_minutes += self.flight.airborne_minutes
