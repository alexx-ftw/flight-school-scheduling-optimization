# Class for storing school information

import datetime

from astral import LocationInfo
from astral.sun import sun

import flightlogger as fl
from classes.aircraft import Aircraft
from classes.user import User

BERRIEL_COORDS = {
    "latitude": 27.782340126048187,
    "longitude": -15.507411291514057,
}
AD_LOC = LocationInfo(
    timezone="Atlantic/Canary",
    latitude=BERRIEL_COORDS["latitude"],
    longitude=BERRIEL_COORDS["longitude"],
)


class School:
    def __init__(self, date: datetime.date) -> None:
        self.date = date
        SUN = sun(AD_LOC.observer, date=self.date, tzinfo=AD_LOC.timezone)
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
