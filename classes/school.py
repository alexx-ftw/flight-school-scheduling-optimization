# Class for storing school information

import datetime

from astral import LocationInfo
from astral.sun import sun

import flightlogger as fl
import my_secrets as secs
from classes.aircraft import Aircraft
from classes.user import User

AD_LOC = LocationInfo(
    timezone="Atlantic/Canary",
    latitude=secs.AD_COORDS["latitude"],
    longitude=secs.AD_COORDS["longitude"],
)


class School:
    def __init__(self, scheduling_date: datetime.date) -> None:
        fl.SCHEDULING_DATE = scheduling_date
        SUN = sun(AD_LOC.observer, date=fl.SCHEDULING_DATE, tzinfo=AD_LOC.timezone)
        fl.SUN = {
            "sunrise": SUN["sunrise"],
            "sunset": SUN["sunset"],
        }

        self.aircrafts: list[Aircraft] = []
        self.instructors: list[User] = []
        self.students: list[User] = []
        self.role_groups = [self.instructors, self.students]

    def update(self) -> None:
        """
        Update the data of the school.
        """
        self.role_groups = [self.instructors, self.students]

    def get_users(self) -> None:
        """
        Get the users.
        """
        self.instructors = fl.get_users_by_role("INSTRUCTOR")
        self.students = fl.get_users_by_role("STUDENT")
        self.update()

        # Remove users with CallSign:
        unwanted_callsigns = ["SENASA", "AUSTRO", "Instructor"]
        for group in self.role_groups:
            group[:] = [
                user for user in group if user.call_sign not in unwanted_callsigns
            ]
