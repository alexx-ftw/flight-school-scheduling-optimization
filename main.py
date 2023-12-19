"""
This program will solve the problem of finding the optimal scheduling for a given day considering
aircrafts, instructors and students of a flight school.
The program will use the FlightLogger API to get the data of the aircrafts, instructors and students.
The program will use the Google OR-Tools to solve the problem.
"""
import datetime
from typing import Union

import pytz
import tabulate

import flightlogger as fl
from classes.school import School

# Scheduling for date
scheduling_date = datetime.date(2023, 12, 21)

TODAY = datetime.date.today()

# Create the school object
canavia = School(scheduling_date=scheduling_date)


# Startup
def main() -> None:
    """Main function."""

    # Get the aircrafts
    canavia.aircrafts = fl.get_aircrafts()

    # Convert the list of aircrafts to a list of dictionaries
    aircrafts_data = [aircraft.__dict__ for aircraft in canavia.aircrafts]

    # Print the aircrafts using tabulate library
    print(tabulate.tabulate(aircrafts_data, headers="keys", tablefmt="fancy_grid"))

    # Get the users
    canavia.get_users()

    # Sort instructors by total airborne minutes flow since the start of the month
    canavia.instructors.sort(key=lambda x: x.airborne_time_mtd, reverse=True)

    # Sort students by last flight time
    canavia.students.sort(
        key=lambda x: x.flights[0].off_block
        if x.flights
        else datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC),
        reverse=True,
    )
    # Sort students by call sign
    # canavia.students.sort(key=lambda x: x.call_sign)

    # Print the users using tabulate library by groups. Only those who are available.
    for role_group in canavia.role_groups:
        users_data: list[dict[str, Union[str, int]]] = []
        for user in role_group:
            if user.is_available:
                print_dict = {
                    "CallSign": user.call_sign,
                }
                if user.is_instructor:
                    # Airborne time since the start of the month. No decimals.
                    print_dict[
                        "AirborneTimeMTD"
                    ] = f"{(user.airborne_time_mtd // 3600):.0f}h {((user.airborne_time_mtd % 3600) // 60):.0f}m"

                # Each program name will be printed in a new line
                print_dict["Programs"] = "\n".join(
                    [program.name for program in user.programs]
                )
                # TODO (eros): Get the last flight time from the latest booking instead of the last flight.
                # Last flight time in days from today. No hours or minutes.
                if user.is_student:
                    print_dict["LastFlight"] = (
                        str((TODAY - user.flights[0].off_block.date()).days)
                        if user.flights
                        else ""
                    )

                users_data.append(print_dict)  # type: ignore
        print("\n\n\n\n\n")
        print(tabulate.tabulate(users_data, headers="keys", tablefmt="fancy_grid"))


if __name__ == "__main__":
    main()
