"""
This module will be used to store the User objects.
"""
from datetime import datetime
from typing import Any

import flightlogger as fl
from classes.availability_slot import AvailabilitySlot
from classes.flight import Flight
from classes.program import Program


class User(object):
    """
    This class will be used to store the User objects.
    """

    def __init__(
        self,
        call_sign: str,
        type: str,
        fl_id: str,
        address: str,
        city: str,
        zipcode: str,
    ) -> None:
        self.call_sign = call_sign
        self.type: str = type
        if self.type == "INSTRUCTOR":
            self.is_instructor = True
            self.is_student = False
        elif self.type == "STUDENT":
            self.is_student = True
            self.is_instructor = False
        self.id = fl_id
        self.address = address
        self.city = city
        self.zipcode = zipcode

        self.programs: list[Program] = []
        self.flights: list[Flight] = []
        self.total_airborne_minutes: float = 0
        self.availabilities: list[AvailabilitySlot] = []
        from classes.booking import Booking

        self.bookings: list[Booking] = []
        self.is_available: bool
        self.data: dict[str, Any]
        self.airborne_time_mtd: float = 0

        from classes.classes import Class

        self.classes: list[Class] = []

        self.days_since_last_flight: int = 0

    def initialize(self) -> None:
        """
        Initialize the user.
        """
        self.set_flights()
        self.set_availabilities()
        self.set_programs()
        self.set_bookings()

        # ! CALCULATIONS FOR THE TABLE PRINTING
        # Calculate days since last flight or booking from day of scheduling
        # If the user has any bookings, use the last booking
        # If the user has no bookings, use the last flight.
        if self.bookings:
            self.days_since_last_flight = (
                fl.SCHEDULING_DATE - self.bookings[0].starts_at.date()
            ).days
        elif self.flights:
            self.days_since_last_flight = (
                fl.SCHEDULING_DATE - self.flights[0].off_block.date()
            ).days

        # Sum the airborne minutes of all flights that are after
        # the start of the month of the scheduling date to the scheduling date
        # and all the airborne minutes of the bookings that are after the start
        # of the month of the scheduling date to the scheduling date
        self.airborne_time_mtd = sum(
            flight.airborne_time
            for flight in self.flights
            if flight.off_block.date() >= fl.SCHEDULING_DATE.replace(day=1)
            and flight.off_block.date() <= fl.SCHEDULING_DATE
        ) + sum(
            booking.flight_data.airborne_time
            for booking in self.bookings
            if booking.starts_at.date() >= fl.SCHEDULING_DATE.replace(day=1)
            and booking.starts_at.date() <= fl.SCHEDULING_DATE
        )

        # Calculate airborne time on the scheduling date
        self.airborne_time_scheduling_date = (
            sum(
                flight.airborne_time
                for flight in self.flights
                if flight.off_block.date() == fl.SCHEDULING_DATE
            )
            + sum(
                booking.flight_data.airborne_time
                for booking in self.bookings
                if booking.starts_at.date() == fl.SCHEDULING_DATE
            )
        ) / 60

    def set_flights(self) -> None:
        """
        Get the flights that the user has flown.
        """
        for flight in self.data["flights"]["nodes"]:  # type: ignore
            self.flights.append(
                # Format of the off block time is "YYYY-MM-DDTHH:MM:SSZ"
                # Convert it to a datetime object
                Flight(
                    off_block=datetime.fromisoformat(flight["offBlock"]),  # type: ignore
                    on_block=datetime.fromisoformat(flight["onBlock"]),  # type: ignore
                    airborne_time=(
                        datetime.fromisoformat(flight["onBlock"])
                        - datetime.fromisoformat(flight["offBlock"])
                    ).total_seconds()
                    / 60,
                )
            )

        # Sort the flights by off block time from latest to earliest
        # Format of the off block time is "YYYY-MM-DDTHH:MM:SSZ"
        self.flights.sort(key=lambda x: x.off_block, reverse=True)

    def set_availabilities(self) -> None:
        """
        Check if the user is available between two datetimes.
        """
        # Convert the availabilities to AvailabilitySlot objects
        for availability in self.data["availabilities"]["nodes"]:  # type: ignore
            self.availabilities.append(
                AvailabilitySlot(
                    starts_at=datetime.fromisoformat(availability["startsAt"]),
                    ends_at=datetime.fromisoformat(availability["endsAt"]),
                    unavailable=bool(availability["unavailable"]),
                )
            )

        # User is available if:
        # - At least one availability slot is not unavailable
        # - and that availability slot is not included inside a bigger availability slot that is unavailable
        # - and the SCHEDULING_DATE is after or equal to the start date of the availability slot
        # - and the SCHEDULING_DATE is before or equal to the end date of the availability slot
        self.is_available = (
            any(
                not availability.unavailable
                and not any(
                    availability_2.starts_at <= availability.starts_at
                    and availability_2.ends_at >= availability.ends_at
                    and availability_2.unavailable
                    for availability_2 in self.availabilities
                )
                and fl.SCHEDULING_DATE >= availability.starts_at.date()
                and fl.SCHEDULING_DATE <= availability.ends_at.date()
                for availability in self.availabilities
            )
            if self.availabilities
            else False
        )

    def set_programs(self) -> None:
        """
        Get the programs that the user is enrolled in.
        """
        # Convert the programs to Program objects
        for program in self.data["userPrograms"]["nodes"]:  # type: ignore
            self.programs.append(Program(name=program["program"]["name"]))

    def set_bookings(self) -> None:
        """
        Get the bookings that the user has made.
        """
        # Convert the bookings to Booking objects
        for booking in (
            self.data["bookings"]["nodes"] if self.data.get("bookings") else []
        ):
            from classes.booking import Booking

            self.bookings.append(
                Booking(
                    starts_at=datetime.fromisoformat(booking["startsAt"]),
                    ends_at=datetime.fromisoformat(booking["endsAt"]),
                    comment=booking["comment"],
                    id=booking["id"],
                    status=booking["status"],
                    instructor=booking["instructor"]["callSign"],
                    student=booking["student"]["callSign"],
                    flight_data=Flight(
                        off_block=datetime.fromisoformat(booking["flightStartsAt"]),
                        on_block=datetime.fromisoformat(booking["flightEndsAt"]),
                        airborne_time=(
                            datetime.fromisoformat(booking["flightEndsAt"])
                            - datetime.fromisoformat(booking["flightStartsAt"])
                        ).total_seconds(),
                    ),
                )
            )
