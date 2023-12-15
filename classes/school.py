# Class for storing school information

from flightlogger import FlightLogger


class School:
    def __init__(self) -> None:
        self.FL = FlightLogger()
        self.aircrafts = self.FL.get_aircrafts()
