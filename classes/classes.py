"""
This file stores the information about the FlightLogger Classes
"""

from dataclasses import dataclass

from classes.user import User


@dataclass
class Class(object):
    """
    Class for storing Classes information.
    """

    name: str
    users: list[User]
