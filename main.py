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

import tabulate
import termcolor

from classes.aircraft import Aircraft
from classes.school import School
from classes.user import User


def print_user_groups(users: list[User]) -> None:
    """
    Print the users in groups.

    Args:
        school (School): The school object containing the user groups.

    Returns:
        None
    """
    table_data: list[dict[str, Union[str, int]]] = []
    for user in users:
        if user.is_available:
            print_dict = {
                "CallSign": user.call_sign,
            }
            # ! INSTRUCTORS SPECIFIC
            if user.is_instructor:
                # Airborne time since the start of the month. No decimals.
                print_dict["AirTimeMTD"] = (
                    f"{(user.airborne_time_mtd_minutes // 60):.0f}h "
                    + f"{(user.airborne_time_mtd_minutes % 60):.0f}m"
                )
                # Airborne time on the scheduling date. No decimals.
                # Print the airborne time in HOURS and MINUTES

                print_dict["AirTimeSCHDate"] = termcolor.colored(
                    f"{(user.airborne_time_on_scheduling_date // 60):.0f}h"
                    + f" {(user.airborne_time_on_scheduling_date % 60):.0f}m",
                    "dark_grey",
                )
                # Print the "Tiredness" factor.
                # Red if < 60, dark_grey if >= 60, red if >= 90
                # If 0, print nothing
                color = (
                    "red"
                    if user.tiredness >= 90 or user.tiredness < 60
                    else "dark_grey"
                )
                print_dict["Tiredness"] = (
                    termcolor.colored(f"{user.tiredness:.0f}", color)
                    if user.tiredness != 0
                    else ""
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
                    classes_list.append(termcolor.colored("DETECTED - Tenerife", "red"))

                # If "TENERIFE" in any of the classes, print it in YELLOW color
                classes_list.extend(
                    termcolor.colored(class_.name, "yellow")
                    for class_ in user.classes
                    if "tenerife" in class_.name.lower()
                )
                # If "TIME CONSTRAINED" in any of the classes, print it in RED color
                classes_list.extend(
                    termcolor.colored(class_.name, "red")
                    for class_ in user.classes
                    if "TIME CONSTRAINED" in class_.name
                )
                # Include the rest of the classes
                classes_list.extend(
                    class_.name
                    for class_ in user.classes
                    if "tenerife" not in class_.name.lower()
                    and "CONSTRAINED" not in class_.name
                )
                print_dict["Classes"] = "\n".join(classes_list)
                print_dict["DaysSinceLastFlight"] = (
                    str(user.days_since_last_flight)
                    if user.days_since_last_flight != -999
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


def print_aircrafts(aircrafts: list[Aircraft]) -> None:
    """
    Print the aircrafts."""

    # Print the aircrafts using tabulate library
    print(
        tabulate.tabulate(
            [
                {
                    "Aircraft": aircraft.call_sign,
                    "TotalAirborneTime": f"{(aircraft.total_airborne_minutes // 60):.0f}h "
                    + f"{(aircraft.total_airborne_minutes % 60):.0f}m",
                    # Scheduled flight hours on the scheduling date
                    "ScheduledFlightTime": f"{(aircraft.sch_date_booked_flight_minutes // 60):.0f}h "
                    + f"{(aircraft.sch_date_booked_flight_minutes % 60):.0f}m",
                }
                for aircraft in aircrafts
            ],
            headers="keys",
            tablefmt="fancy_grid",
        )
    )


# Startup
async def scheduler() -> None:
    """Main function."""
    # Clear the screen
    print("\033c")
    global scheduling_date
    print(
        f"{SCHEDULING_DATE_LABEL} {scheduling_date} {calendar.day_name[scheduling_date.weekday()]}"
    )

    # Create the school object
    canavia = School(scheduling_date=scheduling_date)
    await canavia.initialize()

    # Remove users with CallSign:
    unwanted_callsigns = ["SENASA", "AUSTRO", "Instructor", "EVESC"]
    for group in canavia.role_groups:
        group[:] = [user for user in group if user.call_sign not in unwanted_callsigns]

    # Leave only students that have a class that includes "PUEDE VOLAR"
    canavia.students[:] = [
        student
        for student in canavia.students
        if any(
            "PUEDE VOLAR" in class_.name for class_ in student.classes if class_.name
        )
    ]

    # Sort instructors by airborne time MTD
    canavia.instructors.sort(key=lambda x: x.airborne_time_mtd_minutes)
    # If two instructors are within 6 hours of airborne time of each other,
    # sort those by tiredness without changing the order of the rest of the instructors
    for i in range(len(canavia.instructors) - 1):
        if (
            canavia.instructors[i + 1].airborne_time_mtd_minutes
            - canavia.instructors[i].airborne_time_mtd_minutes
            <= 6 * 60
        ):
            canavia.instructors[i : i + 2] = sorted(
                canavia.instructors[i : i + 2], key=lambda x: x.tiredness
            )

    # Sort students by days since last flight. Put students with "TIME CONSTRAINED" in
    # any of their classes at the beginning of the list
    canavia.students.sort(key=lambda x: x.days_since_last_flight, reverse=True)
    canavia.students.sort(
        key=lambda x: any("CONSTRAINED" in class_.name for class_ in x.classes),
        reverse=True,
    )

    # Remove any class that does not start with "z" from the students
    for student in canavia.students:
        student.classes[:] = [
            class_ for class_ in student.classes if class_.name.startswith("z")
        ]

    # Print the aircrafts
    print_aircrafts(canavia.aircrafts)

    # Print instructors and students
    print_user_groups(canavia.instructors)
    print_user_groups(canavia.students)

    # ! PRINT WARNINGS
    for warning in canavia.warnings:
        print(warning)

    # Restart the program
    global start
    start = False


def is_active_window() -> bool:
    """Check if the console is the active window."""
    # If the program is being debugged, return True
    if debugging:
        return True

    # Use ctypes
    import ctypes

    # Get the handle of the active window
    handle = ctypes.windll.user32.GetForegroundWindow()
    # Get the title of the active window
    window_title = ctypes.create_string_buffer(255)
    ctypes.windll.user32.GetWindowTextA(handle, ctypes.byref(window_title), 255)
    # Convert the title to a string, handling decoding errors
    try:
        title = window_title.value.decode("utf-8")
    except UnicodeDecodeError:
        title = ""

    # Check if the title is "Command Prompt"
    return title in {"Command Prompt", "Windows PowerShell"}


def increase_date() -> None:
    """Increase the scheduling date by 1 day."""
    # Check if the console is the active window
    if is_active_window():
        global scheduling_date
        scheduling_date += datetime.timedelta(days=1)
        print(
            SCHEDULING_DATE_LABEL,
            scheduling_date,
            calendar.day_name[scheduling_date.weekday()],
            end="\r",
        )
    return None


def decrease_date() -> None:
    """Decrease the scheduling date by 1 day."""
    # Check if the console is the active window
    if is_active_window():
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

    return None


start = False


def main(skip_instructions: bool = False) -> None:
    """Print the instructions."""
    if not skip_instructions:
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

    global start
    counter = 0.0
    # After 10 minutes of inactivity, the program will exit
    while not start:
        if counter >= 10 * 60:
            print("\nExiting...")
            global end
            end = True
            return None
        counter += 0.1
        sleep(0.1)

    if start:
        if is_active_window():
            print("Starting...")
            # Run the main function
            import asyncio

            asyncio.run(scheduler())
            skip_instructions = False

        else:
            # print("The console must be the active window.")
            start = False
            skip_instructions = True
        main(skip_instructions)

    return None


debugging = False

if __name__ == "__main__":
    # Clear the screen
    print("\033c")

    # If the "-d" argument is passed, enable debugging
    import sys

    if "-d" in sys.argv:
        debugging = True

    # Use keyboard to control the program
    import keyboard

    keyboard.add_hotkey("right", increase_date)
    keyboard.add_hotkey("left", decrease_date)
    end = False
    keyboard.add_hotkey("esc", lambda: globals().update(end=True))
    # Enter to start the program
    keyboard.add_hotkey("enter", lambda: globals().update(start=True))

    # Scheduling for date
    TODAY = datetime.date.today()
    scheduling_date = TODAY
    SCHEDULING_DATE_LABEL = "SCHEDULING DATE:"

    # Run the main function

    main()

    print("\nExiting...")
