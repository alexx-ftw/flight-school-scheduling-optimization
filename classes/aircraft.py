"""This class will be used to store Aircraft objects.
"""


class Aircraft(object):
    """
    This class will be used to store Aircraft objects.
    """

    def __init__(
        self,
        fl_id: str,
        call_sign: str,
        total_airborne_minutes: int,
        aircraft_class: str,
    ) -> None:
        self.fl_id = fl_id
        self.call_sign = call_sign
        self.total_airborne_minutes = total_airborne_minutes
        self.aircraft_class = aircraft_class
        from classes.booking import Booking

        self.bookings: list[Booking] = []
        self.sch_date_booked_flight_minutes = 0
