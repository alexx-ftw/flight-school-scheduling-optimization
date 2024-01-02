"""
Class for storing school information
"""
import datetime
from typing import Any

from astral import LocationInfo
from astral.sun import sun
from tqdm import tqdm

import flightlogger as fl
import my_secrets as secs
from classes.aircraft import Aircraft
from classes.classes import Class
from classes.user import User

AD_LOC = LocationInfo(
    timezone="Atlantic/Canary",
    latitude=secs.AD_COORDS["latitude"],
    longitude=secs.AD_COORDS["longitude"],
)


class School(object):
    """
    Class for storing school information.
    """

    def __init__(self, scheduling_date: datetime.date) -> None:
        fl.SCHEDULING_DATE = scheduling_date
        SUN = sun(AD_LOC.observer, date=fl.SCHEDULING_DATE, tzinfo=AD_LOC.timezone)
        fl.SUN = {
            "sunrise": SUN["sunrise"],
            "sunset": SUN["sunset"],
        }

        self.classes: list[Class] = []

        self.aircrafts: list[Aircraft]
        self.instructors: list[User]
        self.students: list[User]

        self.warnings: list[str] = []

    async def initialize(self) -> None:
        """
        Initialize the school.
        """
        self.aircrafts = await self.get_aircrafts()

        # Sort the aircrafts by total airborne minutes
        self.aircrafts.sort(
            key=lambda aircraft: aircraft.total_airborne_minutes, reverse=True
        )

        self.instructors = await self.get_instructors()
        self.students = await self.get_students()
        self.role_groups = [self.instructors, self.students]

        await self.get_bookings()
        await self.get_classes()

        for user in self.instructors + self.students:
            warnings = await user.initialize(self.aircrafts)
            self.warnings.extend(warnings)

    @staticmethod
    async def get_aircrafts() -> list[Aircraft]:
        """
        Get the aircrafts.
        """
        print("Getting aircrafts...")
        aircrafts: dict[str, Any] = await fl.get_aircrafts()

        print("Creating aircrafts...")
        return [
            Aircraft(
                fl_id=aircraft["id"],
                call_sign=aircraft["callSign"],
                total_airborne_minutes=aircraft["totalAirborneMinutes"],
                aircraft_class=aircraft["aircraftClass"],
            )
            for aircraft in tqdm(aircrafts)
        ]

    async def get_instructors(self) -> list[User]:
        """
        Get the instructors.
        """
        instructors = await fl.get_users_by_role("INSTRUCTOR")

        return await self.create_users(instructors, "INSTRUCTOR")

    async def get_students(self) -> list[User]:
        """
        Get the students.
        """
        students = await fl.get_users_by_role("STUDENT")

        return await self.create_users(students, "STUDENT")

    async def get_classes(self) -> None:
        """
        Get the classes.
        """
        classes = await fl.get_classes()

        for class_ in classes:
            name = class_["name"]  # type: ignore
            # Specify the type of the users list
            users: list[User] = []
            for user in class_["users"]:  # type: ignore
                for role_group in self.role_groups:
                    users.extend(
                        user_
                        for user_ in role_group
                        if user_.call_sign == user["callSign"]  # type: ignore
                    )
            self.classes.append(Class(name, users))

        for class_ in self.classes:
            for user in class_.users:
                user.classes.append(class_)

    async def get_bookings(self) -> None:
        """
        Get the bookings.
        """
        bookings = await fl.get_bookings()
        # print(json.dumps(bookings, indent=4))

        # Add the bookings to the users data property
        for booking in bookings:
            for role_group in self.role_groups:
                for user in role_group:
                    if user.call_sign in [
                        booking["instructor"]["callSign"],  # type: ignore
                        booking["student"]["callSign"],  # type: ignore
                    ]:
                        # print(json.dumps(user.data, indent=4))
                        try:
                            user.data["bookings"]["nodes"].append(booking)
                        except KeyError:
                            user.data["bookings"] = {"nodes": [booking]}
                        break

    @staticmethod
    async def create_users(users: dict[str, Any], role: str) -> list[User]:
        """
        Create the users from the response JSON.
        """
        # Create the users
        print(f"Creating {role}S...")
        return [
            User(
                call_sign=user["callSign"],
                type=role,
                fl_id=user["id"],
                address=user["contact"]["address"],
                city=user["contact"]["city"],
                zipcode=user["contact"]["zipcode"],
                data=user,
            )
            for user in tqdm(users["users"]["nodes"])
        ]
