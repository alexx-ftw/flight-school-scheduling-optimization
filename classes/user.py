"""
This module will be used to store the User objects.
"""
import math
from datetime import datetime
from typing import Any

import termcolor

import flightlogger as fl
from classes.aircraft import Aircraft
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
        data: dict[str, Any],
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
        self.data: dict[str, Any] = data
        self.airborne_time_mtd_minutes: float = 0

        from classes.classes import Class

        self.classes: list[Class] = []

        self.days_since_last_flight: float = -math.inf

        from classes.training import Training

        self.trainings: list[Training] | None = None

        self.has_booking_on_scheduling_date: bool = False

    async def initialize(self, aircrafts_list: list[Aircraft]) -> list[str]:
        # sourcery skip: list-comprehension
        """
        Initialize the user.
        """
        self.set_flights()
        self.set_availabilities()
        self.set_programs()
        self.set_bookings(aircrafts_list)
        self.set_trainings()

        warnings: list[str] = []
        # If any booking planned lesson is None, warn in RED
        warnings.extend(
            termcolor.colored(
                f"WARNING: {self.call_sign} has a booking with no planned lesson.\n"
                + f"Date: {booking.starts_at.isoformat()}\n",
                "red",
            )
            for booking in self.bookings
            if booking.planned_lesson is None and "Single" in booking.typename
        )
        # ! CALCULATIONS FOR THE TABLE PRINTING
        # Calculate days since last flight or booking from day of scheduling
        # If the user has any bookings, use the last booking
        # If the user has no bookings, use the last flight.
        if self.bookings:
            # Get the latest booking
            self.bookings.sort(key=lambda x: x.starts_at, reverse=True)
            self.days_since_last_flight = (
                fl.SCHEDULING_DATE - self.bookings[0].starts_at.date()
            ).days
        elif self.flights:
            # Get the latest flight
            self.flights.sort(key=lambda x: x.off_block, reverse=True)
            self.days_since_last_flight = (
                fl.SCHEDULING_DATE - self.flights[0].off_block.date()
            ).days

        # Sum the airborne minutes of all flights that are after
        # the start of the month of the scheduling date to the scheduling date
        # and all the airborne minutes of the bookings that are after the start
        # of the month of the scheduling date to the scheduling date
        self.airborne_time_mtd_minutes = sum(
            flight.airborne_minutes
            for flight in self.flights
            if flight.off_block.date() >= fl.SCHEDULING_DATE.replace(day=1)
            and flight.off_block.date() <= fl.SCHEDULING_DATE
        ) + sum(
            booking.flight.airborne_minutes
            for booking in self.bookings
            if booking.starts_at.date() >= fl.SCHEDULING_DATE.replace(day=1)
            and booking.starts_at.date() <= fl.SCHEDULING_DATE
            and not booking.is_solo
            and not booking.is_cancelled
        )

        # Calculate airborne time on the scheduling date
        self.airborne_time_on_scheduling_date = (
            sum(
                flight.airborne_minutes
                for flight in self.flights
                if flight.off_block.date() == fl.SCHEDULING_DATE
            )
            + sum(
                booking.flight.airborne_minutes
                for booking in self.bookings
                if booking.starts_at.date() == fl.SCHEDULING_DATE
                and not booking.is_solo
                and not booking.is_cancelled
            )
            or 0
        )

        # If the user is an instructor, Calculate the "Tiredness" of the user
        # Tiredness is calculated by the following formula:
        # 1. Get the number of bookings in the scheduling date
        # 2. Multiply that number by the flight hours of the bookings
        if self.is_instructor:
            self.tiredness = (
                (
                    self.airborne_time_on_scheduling_date / 60
                    + sum(
                        booking.starts_at.date() == fl.SCHEDULING_DATE
                        and not booking.is_solo
                        and not booking.is_cancelled
                        for booking in self.bookings
                    )
                )
                / 9
                * 100
            ) or 0

        # If there is any booking on the scheduling date, set self.has_booking_on_scheduling_date to True
        self.has_booking_on_scheduling_date = any(
            booking.starts_at.date() == fl.SCHEDULING_DATE and not booking.is_cancelled
            for booking in self.bookings
        )

        return warnings

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
                    airborne_minutes=(
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

    def set_bookings(self, aircrafts: list[Aircraft]) -> None:
        """
        Get the bookings that the user has made.
        """

        # Convert the bookings to Booking objects
        for booking in (  # type: ignore
            self.data["bookings"]["nodes"] if self.data.get("bookings") else []
        ):
            from classes.booking import Booking

            if "Single" in booking["__typename"]:
                self.bookings.append(
                    Booking(
                        starts_at=datetime.fromisoformat(booking["startsAt"]),  # type: ignore
                        ends_at=datetime.fromisoformat(booking["endsAt"]),  # type: ignore
                        comment=booking["comment"] or "",  # type: ignore
                        id=booking["id"],  # type: ignore
                        status=booking["status"],  # type: ignore
                        instructor=booking["instructor"]["callSign"],  # type: ignore
                        student=booking["student"]["callSign"],  # type: ignore
                        flight=Flight(  # type: ignore
                            off_block=datetime.fromisoformat(booking["flightStartsAt"]),  # type: ignore
                            on_block=datetime.fromisoformat(booking["flightEndsAt"]),  # type: ignore
                            airborne_minutes=(  # type: ignore
                                datetime.fromisoformat(booking["flightEndsAt"])  # type: ignore
                                - datetime.fromisoformat(booking["flightStartsAt"])  # type: ignore
                            ).total_seconds()
                            / 60,
                        ),
                        planned_lesson=booking["plannedLesson"],  # type: ignore
                        aircraft=next(
                            (
                                aircraft
                                for aircraft in aircrafts
                                if aircraft.call_sign == booking["aircraft"]["callSign"]
                            ),
                        ),
                        typename=booking["__typename"],  # type: ignore
                    )
                )
            elif "Rental" in booking["__typename"]:
                self.bookings.append(
                    Booking(
                        starts_at=datetime.fromisoformat(booking["startsAt"]),  # type: ignore
                        ends_at=datetime.fromisoformat(booking["endsAt"]),  # type: ignore
                        comment=booking["comment"] or "",  # type: ignore
                        id=booking["id"],  # type: ignore
                        status=booking["status"],  # type: ignore
                        renter=booking["renter"]["callSign"],  # type: ignore
                        flight=Flight(
                            off_block=datetime.fromisoformat(booking["flightStartsAt"]),  # type: ignore
                            on_block=datetime.fromisoformat(booking["flightEndsAt"]),  # type: ignore
                            airborne_minutes=(
                                datetime.fromisoformat(booking["flightEndsAt"])  # type: ignore
                                - datetime.fromisoformat(booking["flightStartsAt"])  # type: ignore
                            ).total_seconds()
                            / 60,
                        ),
                        aircraft=next(
                            (
                                aircraft
                                for aircraft in aircrafts
                                if aircraft.call_sign == booking["aircraft"]["callSign"]
                            ),
                        ),
                        typename=booking["__typename"],  # type: ignore
                    )
                )
            elif "Operation" in booking["__typename"]:
                self.bookings.append(
                    Booking(
                        starts_at=datetime.fromisoformat(booking["startsAt"]),  # type: ignore
                        ends_at=datetime.fromisoformat(booking["endsAt"]),  # type: ignore
                        comment=booking["comment"] or "",  # type: ignore
                        id=booking["id"],  # type: ignore
                        status=booking["status"],  # type: ignore
                        pic=booking["pic"]["callSign"],  # type: ignore
                        flight=Flight(
                            off_block=datetime.fromisoformat(booking["flightStartsAt"]),  # type: ignore
                            on_block=datetime.fromisoformat(booking["flightEndsAt"]),  # type: ignore
                            airborne_minutes=(
                                datetime.fromisoformat(booking["flightEndsAt"])  # type: ignore
                                - datetime.fromisoformat(booking["flightStartsAt"])  # type: ignore
                            ).total_seconds()
                            / 60,
                        ),
                        aircraft=next(
                            (
                                aircraft
                                for aircraft in aircrafts
                                if aircraft.call_sign == booking["aircraft"]["callSign"]
                            ),
                        ),
                        typename=booking["__typename"],  # type: ignore
                    )
                )

    def set_trainings(self) -> None:
        """
        Get the trainings that the user has done.
        """
        # Set self.trainings to an empty list if the user has a trainings key
        self.trainings = [] if self.data.get("trainings") else None

        if self.trainings is not None:
            # Convert the trainings to Training objects
            for training in self.data["trainings"]["nodes"]:
                from classes.training import Training

                self.trainings.append(
                    Training(
                        id=training["id"],
                        name=training["name"],
                        status=training["status"],
                        program=training["userProgram"],
                        lecture=training["lecture"],
                        # Set booked to True if any of the bookings planned lesson lecture name
                        # is the same as the training name
                        booked=any(
                            booking.planned_lesson["lecture"]["name"]
                            == training["name"]
                            for booking in self.bookings
                            if booking.planned_lesson is not None
                        ),
                    )
                )

            # Sort the trainings phase from lowest to highest and then by name
            self.trainings.sort(key=lambda x: (x.order, x.name))
