"""
Python file to store all the secrets
This file is in .gitignore so it will not be pushed to github

Scheduling Directives
It will take into consideration the following constraints:
- The flight instructors should not fly more than 4,5 hours per day, and must not fly more than 7 hours per day.
- The students must not fly more than 4 hours per day.
- The instructors should have a 15 minutes incremetal break between flights, for each hour of flight.
- The first flight of the day should start at 8:00 AM, not including the briefing time. Never before the sunrise time.
- The last flight of the day should end at the sunset time, not including the debriefing time, or before.
- The flights should be scheduled inside the Availability window of the instructors and students.
- The flights must never be longer than the remaining time before maintenance of the aircraft.
- The flights must be scheduled inside of the students Availability window.
- If there is another aircraft scheduled for departing at the same time,
there must be a 15 minutes gap between the flights.
- There should be always 1 Tecnam P2008, 1 Tecnam P2006, and 1 Cessna 150 that will not be used for training,
and will be available as a backup should one of the other aircrafts be unavailable unexpectedly or have a
problem which does not allow it to fly.
- The Cessna 150's can not be used for Instrument Rating (IR) training.
- The Tecnam P2008 should be used for Private Pilot License (PPL) training.
- The Tecnam P2006 should be used for Commercial Pilot License (CPL) training only if the mission is Multi Engine (ME).
- The Pipistrel is the only one that can do UPRT Advanced training.
- Basic UPRT training can be done with any aircraft.
- Mario Pons should be scheduled only when absolutely necessary. If in a P2006, it should be the EC-OAD.
He has all the ratings. He is an examiner.
- Raul Vallejo should be scheduled mostly in the EC-OAD Tecnam P2006 for ME training.
He has all the ratings. He is an examiner. Exams should be scheduled with him unless he is not available.
- Sergio Sanchez should be scheduled mostly in the YL-VIP Tecnam P2006 for ME training.
He has all the ratings. He is an examiner.
- PPL students should be scheduled on a P2008, unless none is available.
"""
# FlightLogger API key
# Token to access the FlightLogger API
# trunk-ignore(bandit/B105)
TOKEN = "5bcf165798717accc04674c09340bdfa"

# Airport Coordinates
AD_COORDS = {
    "latitude": 27.782340126048187,
    "longitude": -15.507411291514057,
}
