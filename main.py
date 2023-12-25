"""
This program will solve the problem of finding the optimal scheduling for a given day considering
aircrafts, instructors and students of a flight school.
The program will use the FlightLogger API to get the data of the aircrafts, instructors and students.
The program will use the Google OR-Tools to solve the problem.
"""
import asyncio
import calendar
import datetime
from time import sleep
from typing import Union

import keyboard
import pytz
import tabulate
import termcolor

from classes.school import School


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
                    # If ("Tenerife" in address or city, or "38" in zipcode) and NOT has a class with "Tenerife",
                    classes_list: list[str] = []
                    if (
                        "tenerife" in user.address.lower()
                        or "tenerife" in user.city.lower()
                        or "38" in user.zipcode
                    ) and all(
                        "tenerife" not in class_.name.lower() for class_ in user.classes
                    ):
                        # then include "DETECTED - Tenerife" in RED color in the Classes
                        classes_list.append(
                            termcolor.colored("DETECTED - Tenerife", "red")
                        )

                    # If "TENERIFE" in any of the classes, print it in YELLOW color
                    classes_list.extend(
                        [
                            termcolor.colored(class_.name, "yellow")
                            if "tenerife" in class_.name.lower()
                            else class_.name
                            for class_ in user.classes
                        ]
                    )
                    print_dict["Classes"] = "\n".join(classes_list)
                    print_dict["LastFlight"] = (
                        str((TODAY - user.flights[0].off_block.date()).days)
                        if user.flights
                        else ""
                    )

                table_data.append(print_dict)  # type: ignore
        # Limit string length to 25 characters for the column "Programs"
        # First separate the string by \n, then limit the length of each string
        for row in table_data:
            if "Programs" in row:
                # Ensure "Programs" is a string
                programs: str = str(row["Programs"])
                row["Programs"] = "\n".join(
                    [
                        f"{program[:25]}..." if len(program) > 25 else program
                        for program in programs.split("\n")
                    ]
                )
        print("\n\n\n\n\n")
        print(tabulate.tabulate(table_data, headers="keys", tablefmt="fancy_grid"))


# Startup
async def main() -> None:
    """Main function."""

    # Print the scheduling date
    global scheduling_date

    # Create the school object
    canavia = School(scheduling_date=scheduling_date)

    # Get the aircrafts and print them
    await canavia.get_aircrafts()
    # Convert the list of aircrafts to a list of dictionaries
    aircrafts_data = [aircraft.__dict__ for aircraft in canavia.aircrafts]
    # Print the aircrafts using tabulate library
    print(tabulate.tabulate(aircrafts_data, headers="keys", tablefmt="fancy_grid"))

    # Get the users
    await canavia.get_users()
    # Remove users with CallSign:
    unwanted_callsigns = ["SENASA", "AUSTRO", "Instructor"]
    for group in canavia.role_groups:
        group[:] = [user for user in group if user.call_sign not in unwanted_callsigns]

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

    # Get the classes
    await canavia.get_classes()

    # Leave only students with a class that includes "PUEDE VOLAR"
    canavia.students[:] = [
        student
        for student in canavia.students
        if any(
            "PUEDE VOLAR" in class_.name for class_ in student.classes if class_.name
        )
    ]

    # Remove any class that does not start with "z" from the students
    for student in canavia.students:
        student.classes[:] = [
            class_ for class_ in student.classes if class_.name.startswith("z")
        ]

    # Update the school
    canavia.update()

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
    print(
        "RIGHT_ARROW: Increase date by 1 day\tLEFT_ARROW: Decrease date by 1 day\tEsc: Exit"
    )
    # Print the scheduling date and day
    print(
        SCHEDULING_DATE_LABEL,
        scheduling_date,
        calendar.day_name[scheduling_date.weekday()],
        end="\r",
    )


start = False


def start_program() -> None:
    """Start the program."""
    global start
    start = True


if __name__ == "__main__":
    # Clear the screen
    print("\033c")

    # Use the keyboard library to change the schedule the date
    # "Right arrow" key will increase by 1 the day of the scheduling
    # "Left arrow" key will decrease by 1 the day of the scheduling
    # Enter key will start the program
    keyboard.add_hotkey("right", increase_date)
    keyboard.add_hotkey("left", decrease_date)
    keyboard.add_hotkey("enter", start_program)

    # Scheduling for date
    TODAY = datetime.date.today()
    scheduling_date = TODAY
    SCHEDULING_DATE_LABEL = "SCHEDULING DATE:"

    print_instructions()

    while not start:
        sleep(0.1)

    # Start the program by calling the main function
    asyncio.run(main())

    keyboard.unhook_all()
    print("\nExiting...")
