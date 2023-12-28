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
                # ! INSTRUCTORS SPECIFIC
                if user.is_instructor:
                    # Airborne time since the start of the month. No decimals.
                    print_dict[
                        "AirborneTimeMTD"
                    ] = f"{(user.airborne_time_mtd // 3600):.0f}h {((user.airborne_time_mtd % 3600) // 60):.0f}m"
                    # Airborne time on the scheduling date. No decimals.
                    # Color the airborne time in yellow if between (4.5 and 5.5] hours in minutes
                    # Color the airborne time in red if more than 5.5 hours in minutes
                    # Print the airborne time in HOURS and MINUTES
                    if user.airborne_time_on_scheduling_date <= 4.5 * 60:
                        color = None
                    elif user.airborne_time_on_scheduling_date <= 5.5 * 60:
                        color = "yellow"
                    else:
                        color = "red"

                    print_dict["AirborneTimeSchedulingDate"] = termcolor.colored(
                        f"{(user.airborne_time_on_scheduling_date // 60):.0f}h"
                        + f" {(user.airborne_time_on_scheduling_date % 60):.0f}m",
                        color,
                    )

                # Each program name will be printed in a new line
                print_dict["Programs"] = "\n".join(
                    [program.name for program in user.programs]
                )
                # ! STUDENTS SPECIFIC
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
                    print_dict["DaysSinceLastFlight"] = str(user.days_since_last_flight)

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

    # Get the classes
    await canavia.get_classes()

    # Get the bookings
    await canavia.get_bookings()

    # Initialize the users
    for user in canavia.instructors + canavia.students:
        user.initialize()

    # Leave only students with a class that includes "PUEDE VOLAR"
    canavia.students[:] = [
        student
        for student in canavia.students
        if any(
            "PUEDE VOLAR" in class_.name for class_ in student.classes if class_.name
        )
    ]

    # Sort instructors by airborne time
    canavia.instructors.sort(key=lambda x: x.airborne_time_mtd)

    # Sort students by days since last flight
    canavia.students.sort(key=lambda x: x.days_since_last_flight, reverse=True)

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
