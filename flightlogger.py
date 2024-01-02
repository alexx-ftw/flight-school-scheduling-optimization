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

import my_secrets as secs

transport = AIOHTTPTransport(
    url="https://api.flightlogger.net/graphql",
    headers={"Authorization": f"{secs.TOKEN}"},
)

api_client = Client(transport=transport, fetch_schema_from_transport=True)

SUN: dict[str, datetime.datetime] = {}
SCHEDULING_DATE: datetime.date = datetime.date.today()


async def send_request(
    body: str,
    head: str = "",
    params: dict[str, Any] | None = None,
    page: int = 0,
) -> dict[str, Any]:
    """
    Send a request to the FlightLogger API.
    """
    query = head + body
    try:
        # Send the request to the FlightLogger API
        response_json = await api_client.execute_async(  # type: ignore
            gql(query), variable_values=params
        )  # type: ignore

    except (TransportError, TransportServerError, ClientResponseError):
        print("Error sending the request. Retrying in 5 seconds...")
        sleep(5)
        response_json = await send_request(head=head, body=body, params=params)

    # Take the first parameter of the response as the query object.
    query_object = list(response_json.keys())[0]

    # If there are more pages, get them
    has_next_page = (
        bool(response_json[query_object]["pageInfo"]["hasNextPage"])
        if params
        else False
    )
    if has_next_page and params:
        page += 1
        end_cursor = response_json[query_object]["pageInfo"]["endCursor"]
        params["after"] = end_cursor
        print(f"Getting page {page} with after={end_cursor}...")
        if "after" not in head:
            head = head.replace("(", "($after: String,")
        if "after" not in body:
            body = body.replace("(", "(after: $after,", 1)
        additional_data = await send_request(
            head=head, body=body, params=params, page=page
        )
        response_json[query_object]["nodes"] += additional_data[query_object]["nodes"]

    return response_json


async def get_aircrafts() -> dict[str, Any]:
    """
    Get the aircrafts.
    """

    # Query to get the aircrafts data
    query = """
        {
            aircraft{
                pageInfo{
                    endCursor
                    hasNextPage
                }
                nodes {
                    id
                    callSign
                    totalAirborneMinutes
                    aircraftClass
                }
            }
        }
        """

    # Send the request to the FlightLogger API
    # print(json.dumps(response_json, indent=4))
    response_json = await send_request(query)

    return response_json["aircraft"]["nodes"]


async def get_users_by_role(role: str) -> dict[str, Any]:
    """
    Get the users by role.
    """
    # Query to get the instructors data
    num_users = 12
    params = {"roles": [role], "num_users": num_users}

    if role == "INSTRUCTOR":
        flights_from_date = datetime.date.today().replace(day=1)
    else:
        days_ago = datetime.timedelta(days=90)
        flights_from_date = datetime.date.today() - days_ago

    head = """
query Users(
	$roles: [UserRoleEnum!]
    $num_users: Int
)"""
    body = """
{
	users(
		first: $num_users
		roles: $roles

	){
		pageInfo
        {
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

    # Send the request to the FlightLogger API
    print(f"Getting {role.lower()}s...")
    return await send_request(head=head, body=body, params=params)


async def get_classes() -> dict[str, Any]:
    """
    Get the classes.
    """
    query = """
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

    response_json = await send_request(query)

    return response_json["classes"]["nodes"]


async def get_bookings() -> dict[str, Any]:
    """
    Get the bookings.
    """
    query_body = """
{
	bookings(
		all: true
		from: "today_date"
		subtypes: [SINGLE_STUDENT]
	) {
		nodes {
			... on SingleStudentBooking {
				startsAt
				endsAt
				comment
				id
				status
				instructor {
					callSign
				}
				student {
					callSign
				}
				flightStartsAt
				flightEndsAt
				plannedLesson{
					lecture{
						name
					}
				}
				aircraft{
					callSign
				}
			}
		}
		pageInfo {
			endCursor
			hasNextPage
		}
	}
}""".replace("today_date", str(datetime.date.today()))

    query = query_body

    response_json = await send_request(query)

    return response_json["bookings"]["nodes"]
