import re
import requests
from util.util import time_logger

@time_logger
def get_plan_id(source, destination):
    """
    Fetches the plan ID for the route between source and destination airports.

    Args:
    source (str): ICAO code of the source airport.
    destination (str): ICAO code of the destination airport.

    Returns:
    int: Plan ID.
    """
    url = f"https://api.flightplandatabase.com/search/plans?fromICAO={source}&toICAO={destination}"

    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200 and len(response.json()) > 0:
        plan_id = response.json()[0]['id']
        return plan_id
    else:
        print("Failed to retrieve plan ID:", response.status_code)
        return None

@time_logger
def calculate_route_points(source, destination):
    """
    Fetches the route points between source and destination airports.

    Args:
    source (str): ICAO code of the source airport.
    destination (str): ICAO code of the destination airport.

    Returns:
    list of tuples: A list of tuples with (ident, name, latitude, longitude).
    """
    plan_id = get_plan_id(source, destination)
    if plan_id:
        url = f"https://api.flightplandatabase.com/plan/{plan_id}"
        response = requests.get(url)

        if response.status_code == 200:
            route_data = response.json()
            route_points = []

            for node in route_data['route']['nodes']:
                ident = node.get('ident', 'Unknown')
                name = node.get('name', 'Unknown')
                lat = node['lat']
                lon = node['lon']
                route_points.append((ident, name, lat, lon))

            # Extract cruise speed from notes
            notes = route_data.get('notes', '')
            cruise_speed_match = re.search(r'Cruise Speed: (\d+)kts', notes)
            cruise_speed = int(cruise_speed_match.group(1)) if cruise_speed_match else 800  # Default to 800 kts if not found

            return route_points, cruise_speed
        else:
            print("Failed to retrieve route data:", response.status_code)
            return [], 800  # Default cruise speed
    else:
        return [], 800  # Default cruise speed
