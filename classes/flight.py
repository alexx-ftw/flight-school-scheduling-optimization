# Class for storing flight information


import datetime
from dataclasses import dataclass


@dataclass
class Flight:
    off_block: datetime.datetime
    on_block: datetime.datetime
