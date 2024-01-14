from datetime import datetime
from functools import lru_cache
import requests

def find_closest_weather_data(hourly_weather, expected_time):
    """
    Finds the closest hourly weather data to the expected time.

    Args:
    hourly_weather (list): List of hourly weather data.
    expected_time (datetime): Expected time of arrival.

    Returns:
    dict: Closest hourly weather data.
    """
    min_diff = float('inf')
    closest_weather = None
    for weather in hourly_weather:
        hour_time = datetime.strptime(weather['datetime'], '%H:%M:%S')
        hour_time = expected_time.replace(hour=hour_time.hour, minute=hour_time.minute, second=hour_time.second)
        time_diff = abs((hour_time - expected_time).total_seconds())
        if time_diff < min_diff:
            min_diff = time_diff
            closest_weather = weather
    return closest_weather

    

@lru_cache(maxsize=None)
def fetch_weather_data(lat, lon, date_time):
    """
    Fetches weather data for a given latitude, longitude, and datetime.

    Args:
    lat (float): Latitude of the location.
    lon (float): Longitude of the location.
    datetime (str): Date and time in the format 'yyyy-MM-ddTHH:mm:ss'.
    api_key (str): API key for Visual Crossing Weather API.

    Returns:
    dict: Weather data for the specified location and time.
    """
    if not isinstance(date_time, str):
        date_time = datetime.strftime(date_time, '%Y-%m-%dT%H:%M:%S')
    location = f"{lat},{lon}"
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date_time}?key=X58QCAXSNA9STSY88UDWQXF8Q"
    response = requests.get(url)

    if response.status_code == 200:
        weather_data = response.json()
        # Erxtact relevant weather information here
        return find_closest_weather_data(weather_data['days'][0]['hours'], datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S'))
    else:
        print("Failed to retrieve weather data:", response.status_code)
        return {}