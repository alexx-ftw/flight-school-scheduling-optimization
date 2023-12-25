"""
This program will solve the problem of finding the optimal scheduling for a given day considering
aircrafts, instructors and students of a flight school.
The program will use the FlightLogger API to get the data of the aircrafts, instructors and students.
The program will use the Google OR-Tools to solve the problem.
"""
import calendar
import datetime
from time import sleep
from typing import Union

import keyboard
import pytz
import tabulate

import flightlogger as fl
from classes.school import School


def get_and_print_aircrafts(school: School) -> None:
    """Get the aircrafts and print them."""
    # Get the aircrafts
    school.aircrafts = fl.get_aircrafts()

    # Convert the list of aircrafts to a list of dictionaries
    aircrafts_data = [aircraft.__dict__ for aircraft in school.aircrafts]

    # Print the aircrafts using tabulate library
    print(tabulate.tabulate(aircrafts_data, headers="keys", tablefmt="fancy_grid"))


def print_user_groups(school: School) -> None:
    """
    Print the users in groups.

    Args:
        school (School): The school object containing the user groups.

    Returns:
        None
    """
    for role_group in school.role_groups:
        table_data: list[dict[str, Union[str, int]]] = []
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

                table_data.append(print_dict)  # type: ignore
        # Limit string length to 25 characters
        # First separate the string by \n, then limit the length of each string
        for row in table_data:
            for key, value in row.items():
                if isinstance(value, str) and len(value) > 25:
                    row[key] = f"{value[:25]}..."
        print("\n\n\n\n\n")
        print(tabulate.tabulate(table_data, headers="keys", tablefmt="fancy_grid"))


def get_users(school: School) -> None:
    """Get the users and sort them."""
    # Get the users
    school.get_users()

    # Sort instructors by total airborne minutes flow since the start of the month
    school.instructors.sort(key=lambda x: x.airborne_time_mtd, reverse=True)

    # Sort students by last flight time
    school.students.sort(
        key=lambda x: x.flights[0].off_block
        if x.flights
        else datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC),
        reverse=True,
    )
    # Sort students by call sign
    # canavia.students.sort(key=lambda x: x.call_sign)


# Startup
def main() -> None:
    """Main function."""

    # Print the scheduling date
    global scheduling_date

    # Create the school object
    canavia = School(scheduling_date=scheduling_date)

    # Get the aircrafts and print them
    get_and_print_aircrafts(canavia)

    # Get the users
    get_users(canavia)

    # Print the users
    print_user_groups(canavia)

    global finished
    finished = True


def increase_date() -> None:
    """Increase the scheduling date by 1 day."""
    global scheduling_date
    scheduling_date += datetime.timedelta(days=1)
    print(
        SCHEDULING_DATE_LABEL,
        scheduling_date,
        calendar.day_name[scheduling_date.weekday()],
        end="\r",
    )


def decrease_date() -> None:
    """Decrease the scheduling date by 1 day."""
    global scheduling_date
    # Prevent the scheduling date from being before today
    if scheduling_date > TODAY:
        scheduling_date -= datetime.timedelta(days=1)
    print(
        SCHEDULING_DATE_LABEL,
        scheduling_date,
        calendar.day_name[scheduling_date.weekday()],
        end="\r",
    )


def print_instructions() -> None:
    """Print the instructions."""
    print("+: Increase date by 1 day\t-: Decrease date by 1 day\tEsc: Exit")
    # Print the scheduling date and day
    print(
        SCHEDULING_DATE_LABEL,
        scheduling_date,
        calendar.day_name[scheduling_date.weekday()],
        end="\r",
    )


if __name__ == "__main__":
    # Clear the screen
    print("\033c")

    # Use the keyboard library to change the schedule the date
    # + key will increase by 1 the day of the scheduling
    # - key will decrease by 1 the day of the scheduling
    # Enter key will start the program
    keyboard.add_hotkey("+", increase_date)
    keyboard.add_hotkey("-", decrease_date)
    keyboard.add_hotkey("enter", main)

    # Scheduling for date
    TODAY = datetime.date.today()
    scheduling_date = TODAY
    SCHEDULING_DATE_LABEL = "SCHEDULING DATE:"

    print_instructions()

    finished = False
    while not keyboard.is_pressed("esc") and not finished:
        sleep(0.1)

    keyboard.unhook_all()
    print("\nExiting...")
