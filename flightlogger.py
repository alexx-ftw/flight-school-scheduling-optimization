# This FlightLogger class will be used to store the many different objects that will be used in the program.
# It will also be used to make the HTTP requests to the FlightLogger API.
# The FlightLogger class will have the following methods:
# - get_aircrafts() - This method will make an HTTP request to the FlightLogger API to get the aircrafts.
# - get_instructors() - This method will make an HTTP request to the FlightLogger API to get the instructors.
# - get_students() - This method will make an HTTP request to the FlightLogger API to get the students.

# Import the requests library to make HTTP requests

# Import gql library to work with GraphQL


from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from classes.aircraft import Aircraft

# Import the json library to format the JSON responses

# Import the datetime library to work with dates and times

# Token to access the FlightLogger API
TOKEN = "5bcf165798717accc04674c09340bdfa"
transport = AIOHTTPTransport(
    url="https://api.flightlogger.net/graphql", headers={"Authorization": f"{TOKEN}"}
)


class FlightLogger:
    def __init__(self) -> None:
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def get_aircrafts(self) -> list[Aircraft]:
        # Query to get the aircrafts data
        query = gql(
            """
            {
                aircraft{
                    nodes {
                        callSign
                        totalAirborneMinutes
                        aircraftClass
                    }
                }
            }
            """
        )

        # Send the request to the FlightLogger API
        response_json = self.client.execute(query)  # type: ignore

        # Sort the aircrafts by total airborne minutes
        response_json["aircraft"]["nodes"].sort(
            key=lambda aircraft: aircraft["totalAirborneMinutes"],
            reverse=True,
        )

        # Print the response
        # import json
        # print(json.dumps(response_json, indent=4, sort_keys=True))

        aircrafts: list[Aircraft] = []
        for aircraft in response_json["aircraft"]["nodes"]:
            aircrafts.append(
                Aircraft(
                    call_sign=aircraft["callSign"],
                    total_airborne_minutes=aircraft["totalAirborneMinutes"],
                    aircraft_class=aircraft["aircraftClass"],
                )
            )
        return aircrafts
