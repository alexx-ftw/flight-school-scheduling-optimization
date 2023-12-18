# This class will be used to store the User objects.


from datetime import datetime
from typing import Any

from classes.availability_slot import AvailabilitySlot
from classes.flight import Flight
from classes.program import Program


class User:
    def __init__(
        self,
        call_sign: str,
        type: str,
        fl_id: str,
    ) -> None:
        self.call_sign = call_sign
        self.type: str = type
        self.id = fl_id
        self.programs: list[Program] = []
        self.flights: list[Flight] = []
        self.total_airborne_minutes: float = 0
        self.availabilities: list[AvailabilitySlot] = []
        self.is_available: bool
        self.data: dict[str, Any]
        self.airborne_time_mtd: float = 0

    def initialize(self) -> None:
        """
        Initialize the user.
        """
        self.set_flights()
        self.set_availabilities()
        self.set_programs()

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
                )
            )

        # Sort the flights by off block time from latest to earliest
        # Format of the off block time is "YYYY-MM-DDTHH:MM:SSZ"
        self.flights.sort(key=lambda x: x.off_block, reverse=True)

        self.airborne_time_mtd = (
            sum(
                (flight.on_block - flight.off_block).total_seconds()
                for flight in self.flights
                if flight.off_block.month == datetime.now().month
            )
            if self.flights
            else 0
        )

    def set_availabilities(self) -> None:
        """
        Check if the user is available between two datetimes.
        """
        # Convert the availabilities to AvailabilitySlot objects
        for availability in self.data["availabilities"]["nodes"]:  # type: ignore
            self.availabilities.append(
                AvailabilitySlot(
                    starts_at=availability["startsAt"],  # type: ignore
                    ends_at=availability["endsAt"],  # type: ignore
                    unavailable=bool(availability["unavailable"]),  # type: ignore
                )
            )

        # Check if the user is available
        self.is_available = (
            not any(
                availability.unavailable for availability in self.availabilities
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
