# This program will solve the problem of finding the optimal scheduling for a given day considering aircrafts, instructors and students of a flight school.
# The program will use the FlightLogger API to get the data of the aircrafts, instructors and students.
# The program will use the Google OR-Tools to solve the problem.
import datetime

import pytz
import tabulate

import flightlogger as fl
from classes.school import School

# Scheduling for date
date = datetime.date(2023, 12, 19)

# Create the school object
canavia = School(date=date)


# Startup
def main():
    # Get the aircrafts
    canavia.aircrafts = fl.get_aircrafts()

    # Print the aircrafts using tabulate library
    print(tabulate.tabulate(canavia.aircrafts, headers="keys", tablefmt="fancy_grid"))

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
        users_data = []
        for user in role_group:
            if user.is_available:
                users_data.append(  # type: ignore
                    {
                        "CallSign": user.call_sign,
                        # Airborne time since the start of the month. No decimals.
                        "AirborneTimeMTD": f"{(user.airborne_time_mtd // 3600):.0f}h {((user.airborne_time_mtd % 3600) // 60):.0f}m",
                        # Each program name will be printed in a new line
                        "Programs": "\n".join(
                            [program.name for program in user.programs]
                        ),
                        # Availability window/s for the day
                        # "Availability": "\n".join(
                        #     [
                        #         f"{availability.starts_at} - {availability.ends_at}"
                        #         for availability in user.availabilities
                        #     ]
                        # ),
                        # Last flight time
                        "LastFlight": user.flights[0].off_block if user.flights else "",
                    }
                )
        print("\n\n\n\n\n")
        print(tabulate.tabulate(users_data, headers="keys", tablefmt="fancy_grid"))


if __name__ == "__main__":
    main()
