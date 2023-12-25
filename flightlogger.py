"""
FlightLogger API
"""

import datetime
from time import sleep
from typing import Any

from aiohttp.client_exceptions import ClientResponseError
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError, TransportServerError
from graphql import DocumentNode
from tqdm import tqdm

import my_secrets as secs
from classes.aircraft import Aircraft
from classes.user import User

transport = AIOHTTPTransport(
    url="https://api.flightlogger.net/graphql",
    headers={"Authorization": f"{secs.TOKEN}"},
)

api_client = Client(transport=transport, fetch_schema_from_transport=True)

SUN: dict[str, datetime.datetime] = {}
SCHEDULING_DATE: datetime.date = datetime.date.today()


async def send_request(
    query: DocumentNode, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Send a request to the FlightLogger API.
    """
    # Send the request to the FlightLogger API.
    # If there is an error, wait for the time specified in the Retry-After header and try again.
    try:
        response = await api_client.execute_async(query, variable_values=params)  # type: ignore
        response_json = response
    except (TransportError, TransportServerError, ClientResponseError):
        sleep_time = 20
        print(f"Too many requests. Sleeping for {sleep_time} seconds...")
        sleep(sleep_time)
        response_json = await send_request(query, params)
    return response_json


async def get_aircrafts() -> list[Aircraft]:
    """
    Get the aircrafts.
    """

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
    print("Getting aircrafts...")
    response_json = await send_request(query)  # type: ignore

    # Sort the aircrafts by total airborne minutes
    response_json["aircraft"]["nodes"].sort(
        key=lambda aircraft: aircraft["totalAirborneMinutes"],  # type: ignore
        reverse=True,
    )

    aircrafts: list[Aircraft] = [
        Aircraft(
            call_sign=aircraft["callSign"],
            total_airborne_minutes=aircraft["totalAirborneMinutes"],
            aircraft_class=aircraft["aircraftClass"],
        )
        for aircraft in response_json["aircraft"]["nodes"]
    ]
    return aircrafts


def create_users(users: dict[str, Any], role: str) -> list[User]:
    """
    Create the users from the response JSON.
    """
    users_list: list[User] = [
        User(
            call_sign=user["callSign"],
            type=role,
            fl_id=user["id"],
            address=user["contact"]["address"],
            city=user["contact"]["city"],
            zipcode=user["contact"]["zipcode"],
        )
        for user in tqdm(users["users"]["nodes"])
    ]
    # Initialize the users
    for user in tqdm(users_list):
        for user_data in users["users"]["nodes"]:
            if user_data["id"] == user.id:
                user.data = user_data
                user.initialize()

    return users_list


async def get_users_by_role(role: str) -> list[User]:
    """
    Get the users by role.
    """
    # Query to get the instructors data
    num_users = 12
    params = {"roles": [role], "num_users": num_users}

    users: list[User] = []

    if role == "INSTRUCTOR":
        flights_from_date = datetime.date.today().replace(day=1)
    else:
        days_ago = datetime.timedelta(days=90)
        flights_from_date = datetime.date.today() - days_ago

    body_header = """
query Users(
	$roles: [UserRoleEnum!]
    $num_users: Int
)
{
	users(
		first: $num_users
		roles: $roles

	)"""
    body_data = """{
		pageInfo{
		endCursor
		hasNextPage
	}
		nodes{

				callSign
				id
                contact {
                    address
                    city
                    zipcode
                }

			userPrograms
			{
				nodes
				{
					program
					{
						name
					}
				}
			}
			availabilities(
                from: "from_date_scheduling"
            ){
				nodes{
					startsAt
					endsAt
                    unavailable
				}
			}
			flights(
                all:true,
                from: "from_date"
            ){
				nodes{
					offBlock
                    onBlock
                }
			}
        }
	}
}
                """.replace("from_date_scheduling", str(SCHEDULING_DATE)).replace(
        "from_date", str(flights_from_date)
    )

    query_initial = body_header + body_data

    query_after = (
        """
query Users(
    $after: String
    $roles: [UserRoleEnum!]
    $num_users: Int
) {
	users(
		first: $num_users
		after: $after
        roles: $roles
	)
"""
        + body_data
    )

    # Send the request to the FlightLogger API
    page = 1
    print(f"Getting {role.lower()}s page {page}...")
    response_json = await send_request(query=gql(query_initial), params=params)

    users = create_users(response_json, role)

    previous_end_cursor = response_json["users"]["pageInfo"]["endCursor"]

    if response_json["users"]["pageInfo"]["hasNextPage"]:
        print(f"Role {role} has more than 13 users. Getting the rest of the users...")
        params["after"] = response_json["users"]["pageInfo"]["endCursor"]

        while response_json["users"]["pageInfo"]["hasNextPage"]:
            page += 1
            print(f"Getting {role.lower()}s page {page}...")
            response_json = await send_request(query=gql(query_after), params=params)

            print(
                f"Previous endCursor: {previous_end_cursor}. \
                    New endCursor: {response_json['users']['pageInfo']['endCursor']}"
            )
            previous_end_cursor = response_json["users"]["pageInfo"]["endCursor"]

            users += create_users(response_json, role=role)

            params["after"] = response_json["users"]["pageInfo"]["endCursor"]
            print(f"Role {role} size so far: {len(users)}")

    return users


async def get_classes() -> dict[str, Any]:
    """
    Get the classes.
    """
    query = gql(
        """
{
  classes{
		pageInfo{
			hasNextPage
			endCursor
		}
		nodes{
			name
			users{
				callSign
			}
        }
	}
}"""
    )

    response_json = await send_request(query)

    return response_json["classes"]["nodes"]
