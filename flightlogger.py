"""
FlightLogger API
"""

import datetime
import json
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

    try:
        # Send the request to the FlightLogger API
        response_json = await api_client.execute_async(query, variable_values=params)  # type: ignore

        # TODO(eros) Use the cursors list to get the next page.
        # # Check if the query has an "after" parameter in the params dict.
        # # If it does, query the next page accoring to the next cursor in the cursors list.
        # # Merge the responses into one.
        # if params and "after" in params:
        #     # Get the query object
        #     query_object = list(response_json.keys())[0]

        #     # Get the cursors list
        #     with open("cursors.json", "r") as cursors_file:
        #         cursors = json.load(cursors_file)
        #         cursors = dict(cursors)
        #         cursors_list: list[str] = cursors[query_object]["cursors"]

        #     # Get the next cursor
        #     next_cursor = cursors_list[cursors_list.index(params["after"]) + 1]

        #     # Query the next page
        #     params["after"] = next_cursor
        #     print(f"Getting page with cursor {next_cursor}...")
        #     response_json_next_page = await send_request(query, params)

        #     # Merge the responses
        #     response_json[query_object]["nodes"] += response_json_next_page[
        #         query_object
        #     ]["nodes"]

    except (TransportError, TransportServerError, ClientResponseError):
        print("Error sending the request. Retrying in 5 seconds...")
        sleep(5)
        response_json = await send_request(query, params)

    # Take the first parameter of the response as the query object.
    query_object = list(response_json.keys())[0]

    # Check if the response has a "pageInfo" field.
    # If it does, add the endCursor to the cursors list.
    if "pageInfo" in response_json[query_object]:
        with open("cursors.json", "r") as cursors_file:
            # print(cursors_file)
            cursors = json.load(cursors_file)
            # json to dict
            cursors = dict(cursors)
            try:
                cursors_list: list[str] = cursors[query_object]["cursors"]
            except KeyError:
                cursors[query_object] = {"cursors": []}
                cursors_list = cursors[query_object]["cursors"]
            # Pretty print the cursors list
            # print(json.dumps(cursors_list, indent=4))

            # If the endCursor is not in the cursors list, add it.
            if response_json[query_object]["pageInfo"]["endCursor"] not in cursors_list:
                cursors_list.append(
                    response_json[query_object]["pageInfo"]["endCursor"]
                )
                print(
                    f"Added cursor {response_json[query_object]['pageInfo']['endCursor']} to the cursors list."
                )

                # Save the cursors list to the cursors.json file.
                with open("cursors.json", "w") as cursors_file:
                    json.dump(cursors, cursors_file, indent=4)

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
                pageInfo{
                    endCursor
                    hasNextPage
                }
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
