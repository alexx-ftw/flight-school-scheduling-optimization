"""This module has the Flight class"""
import datetime
from dataclasses import dataclass


@dataclass
class Flight(object):
    """
    Class for storing flight data
    """

    briefing_time: datetime.datetime
    off_block: datetime.datetime
    on_block: datetime.datetime
    debriefing_time: datetime.datetime
