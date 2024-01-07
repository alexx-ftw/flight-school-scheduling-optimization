"""
This file contains the class for booking
"""

import datetime
from typing import Any

from attr import dataclass

from classes.aircraft import Aircraft
from classes.flight import Flight
from classes.user import User


@dataclass
class Statuses(object):
    """Class for storing booking statuses"""

    CANCELLED: str = "CANCELLED"
    CONFIRMED: str = "CONFIRMED"
    PENDING: str = "PENDING"


STATUSES = Statuses()


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
        self.is_solo = "solo" in self.comment.lower() or (
            self.planned_lesson is not None
            and "solo" in str(self.planned_lesson["lecture"]["name"]).lower()
        )
        self.id = id
        self.status = status
        self.is_cancelled = self.status == STATUSES.CANCELLED
        self.instructor = instructor
        self.renter = renter
        self.pic = pic
        self.student = student
        self.aircraft = aircraft

        self.aircraft.bookings.append(self)

        self.aircraft.sch_date_booked_flight_minutes += self.flight.airborne_minutes
