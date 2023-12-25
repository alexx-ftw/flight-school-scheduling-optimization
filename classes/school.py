# Class for storing school information

import datetime

from astral import LocationInfo
from astral.sun import sun

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

        self.aircrafts: list[Aircraft] = []
        self.instructors: list[User] = []
        self.students: list[User] = []
        self.role_groups = [self.instructors, self.students]
        self.classes: list[Class] = []

    def update(self) -> None:
        """
        Update the data of the school.
        """
        self.role_groups = [self.instructors, self.students]

    def get_aircrafts(self) -> None:
        self.aircrafts = fl.get_aircrafts()

    def get_users(self) -> None:
        """
        Get the users.
        """
        self.instructors = fl.get_users_by_role("INSTRUCTOR")
        self.students = fl.get_users_by_role("STUDENT")
        self.update()

    def get_classes(self) -> None:
        """
        Get the classes.
        """
        classes = fl.get_classes()

        for class_ in classes:
            name = class_["name"]
            users = []
            for user in class_["users"]:
                for role_group in self.role_groups:
                    users.extend(
                        user_
                        for user_ in role_group
                        if user_.call_sign == user["callSign"]
                    )
            self.classes.append(Class(name, users))

        for class_ in self.classes:
            for user in class_.users:
                user.classes.append(class_)
