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
        aircraft: Aircraft,
        typename: str,
        planned_lesson: dict[str, Any] | None = None,
        instructor: User | None = None,
        renter: User | None = None,
        pic: User | None = None,
        student: User | None = None,
    ) -> None:
        self.typename = typename
        self.starts_at = starts_at
        self.flight = flight
        self.ends_at = ends_at
        self.comment = comment
        self.planned_lesson = planned_lesson
        self.is_solo = self.comment.lower() in {"solo"} or (
            self.planned_lesson is not None
            and str(self.planned_lesson["lecture"]["name"]).lower() in {"solo"}
        )
        self.id = id
        self.status = status
        self.is_cancelled = self.status in {"cancelled"}
        self.instructor = instructor
        self.renter = renter
        self.pic = pic
        self.student = student
        self.aircraft = aircraft

        self.aircraft.bookings.append(self)

        self.aircraft.sch_date_booked_flight_minutes += self.flight.airborne_minutes
