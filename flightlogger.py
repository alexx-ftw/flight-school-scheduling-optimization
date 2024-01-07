"""
Module for storing the FlightLogger API
"""

import datetime
from time import sleep
from typing import Any

from aiohttp.client_exceptions import ClientResponseError
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError, TransportServerError

import my_secrets as secs
from classes.user import User

transport = AIOHTTPTransport(
    url="https://api.flightlogger.net/graphql",
    headers={"Authorization": f"{secs.TOKEN}"},
)

api_client = Client(transport=transport, fetch_schema_from_transport=True)

SUN: dict[str, datetime.datetime] = {}
SCHEDULING_DATE: datetime.date = datetime.date.today()


async def send_request(
    body: str,
    query_object: str,
    head: str = "",
    params: dict[str, Any] | None = None,
    page: int = 0,
    get_next: bool = True,
) -> dict[str, Any]:
    """
    Send a request to the FlightLogger API.
    """
    query = head + body

    # ! Check if we have stored cursors for this query_object

    try:
        # Send the request to the FlightLogger API
        response_json = await api_client.execute_async(  # type: ignore
            gql(query), variable_values=params
        )  # type: ignore

    except (TransportError, TransportServerError, ClientResponseError):
        print("Error sending the request. Retrying in 5 seconds...")
        sleep(5)
        return await send_request(
            body=body,
            query_object=query_object,
            head=head,
            params=params,
            page=page,
            get_next=False,
        )

    # If there are more pages, get them
    has_next_page = (
        bool(response_json[query_object]["pageInfo"]["hasNextPage"]) and get_next
    )
    if has_next_page:
        page += 1
        end_cursor = response_json[query_object]["pageInfo"]["endCursor"]
        if params:
            params["after"] = end_cursor
        else:
            params = {"after": end_cursor}
        print(f"Getting page {page} with after={end_cursor}...")
        # sourcery skip: merge-nested-ifs
        if not head:
            head = f"query {query_object.capitalize()}($after: String)"
        if "after" not in head:
            head = head.replace("(", "($after: String,")
        if "after" not in body:
            body = body.replace("(", "(after: $after,", 1)
        additional_data = await send_request(
            head=head, body=body, params=params, page=page, query_object=query_object
        )
        response_json[query_object]["nodes"] += additional_data[query_object]["nodes"]

    return response_json


async def get_aircrafts() -> dict[str, Any]:
    """
    Get the aircrafts.
    """
    query_object = "aircraft"

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
    response_json = await send_request(query, query_object=query_object)

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

    query_object = "users"
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
    return await send_request(
        head=head, body=body, params=params, query_object=query_object
    )


async def get_classes() -> dict[str, Any]:
    """
    Get the classes.
    """
    query_object = "classes"
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

    response_json = await send_request(query, query_object=query_object)

    return response_json["classes"]["nodes"]


async def get_bookings() -> dict[str, Any]:
    """
    Get the bookings.
    """

    query_object = "bookings"
    query_body = """
{
	bookings(
		all: true
		from: "today_date"
		subtypes: [RENTAL, SINGLE_STUDENT, OPERATION]
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
				__typename
			}
            ... on RentalBooking{
				startsAt
				endsAt
				comment
				id
				status
				flightStartsAt
				flightEndsAt
				aircraft {
					callSign
				}
				renter{
					callSign
				}
				__typename
            }
            ... on OperationBooking{
				startsAt
				endsAt
				comment
				id
				status
				flightStartsAt
				flightEndsAt
				aircraft {
					callSign
				}
				pic{
					callSign
				}
				crew{
					callSign
				}
				__typename
			}
		}
		pageInfo {
			endCursor
			hasNextPage
		}
	}
}""".replace("today_date", str(datetime.date.today()))

    response_json = await send_request(body=query_body, query_object=query_object)

    # print(json.dumps(response_json, indent=4))

    return response_json["bookings"]["nodes"]


async def get_trainings(flyers: list[User]) -> dict[str, Any]:
    """
    Get the trainings using the flyers ids in an async way.
    """
    flyers_ids = [flyer.id for flyer in flyers]
    query_object = "trainings"
    query_body = """
{
	trainings(all: true, status: NOT_FLOWN, userIds: flyers_ids) {
		nodes {
			id
			name
			status
			student {
				callSign
			}
			userProgram{
				name
				status
			}
			lecture{
				vfrDualMinutes
				vfrSoloMinutes
				vfrSimMinutes
				vfrSpicMinutes
				ifrDualMinutes
				ifrSimMinutes
				ifrSpicMinutes
			}
		}
		pageInfo {
			endCursor
			hasNextPage
		}
	}
}
""".replace("flyers_ids", str(flyers_ids)).replace("'", '"')

    response_json = await send_request(body=query_body, query_object=query_object)

    return response_json["trainings"]["nodes"]
