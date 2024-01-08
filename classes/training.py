"""
This file contains the training class.
"""


class Training(object):
    """
    The training class.
    """

    def __init__(
        self,
        id: str,
        name: str,
        status: str,
        program: dict[str, str],
        lecture: dict[str, int],
        booked: bool,
    ) -> None:
        self.id = id
        self.name = name
        self.status = status
        self.program = program
        self.lecture = lecture

        self.order = 0.0
        self.preferred_aircraft = None
        self.required_aircraft = None
        if "PPL" in self.program["name"] or "LAPL" in self.program["name"]:
            self.order = 1
            self.preferred_aircraft = "2008"
        elif "TIME BUILDING" in self.program["name"]:
            self.order = 2
            self.preferred_aircraft = "150"
        elif "IR" in self.program["name"] and "BASIC" in self.program["name"]:
            self.order = 3
            self.required_aircraft = "2008"
        elif "NIGHT" in self.program["name"]:
            self.order = 4
            self.required_aircraft = "2008"
        elif "MEP" in self.program["name"] and "Initial" in self.program["name"]:
            self.order = 5
            self.required_aircraft = "2006"
        elif "IR-MEPL" in self.program["name"] and "Skill" not in self.name:
            self.order = 6
        elif "CPL" in self.program["name"] and "Skill" not in self.name:
            self.order = 7
        elif "Skill" in self.name:
            self.order = 8
        elif "ATP" in self.program["name"]:
            self.order = 99
        elif "FI" in self.program["name"]:
            self.order = 100
            self.preferred_aircraft = "2008"

        self.air_time_minutes = (
            lecture["vfrDualMinutes"]
            or lecture["ifrDualMinutes"]
            or lecture["vfrSoloMinutes"]
            or lecture["vfrSimMinutes"]
            or lecture["ifrSimMinutes"]
            or lecture["ifrSpicMinutes"]
            or lecture["vfrSpicMinutes"]
        )

        self.booked = booked
