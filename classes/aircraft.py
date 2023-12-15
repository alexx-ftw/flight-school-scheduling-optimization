# This class will be used to store Aircraft objects.


from dataclasses import dataclass


@dataclass
class Aircraft:
    call_sign: str
    total_airborne_minutes: int
    aircraft_class: str
