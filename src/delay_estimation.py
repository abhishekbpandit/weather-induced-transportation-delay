from datetime import datetime, timedelta
from util.util import convert_to_icao, haversine, create_input_vector, first_element
from .delay_nlp import estimate_delay_nlp
from .route import calculate_route_points
from .weather_data import fetch_weather_data
from util.util import time_logger

import concurrent.futures
import joblib
import xgboost as xgb
import pandas as pd

# Load the pre-trained XGBoost model
bst = joblib.load('models/my_xgboost.pkl')

def add_dep_time_to_weather_data(weather_data, departure_time, training_columns):
    """
    Adds departure time-related features to the weather data for model input.

    Args:
    - weather_data (dict): Weather data at a certain time.
    - departure_time (datetime): Time of the flight departure.
    - training_columns (list): List of columns used in training the model.

    Returns:
    - dict: Weather data dict updated with time-related features.
    """
    # Convert departure time to individual components
    weather_data.update({
        'hours': departure_time.hour,
        'minutes': departure_time.minute,
        'day': departure_time.day,
        'month': departure_time.month
    })

    # Handle potential list in 'preciptype' and remove 'stations' key
    if isinstance(weather_data['preciptype'], list) and len(weather_data['preciptype']) > 0:
        weather_data['preciptype'] = weather_data['preciptype'][0]

    weather_data.pop('stations', None)

    # Create DataFrame and handle categorical data
    df = pd.DataFrame([weather_data])
    for col in ['preciptype', 'icon', 'month', 'day', 'hours']:
        if col in df.columns:
            df[col] = df[col].apply(first_element).astype('category')

    # One-hot encode and align with training columns
    df_encoded = pd.get_dummies(df, columns=['preciptype', 'icon', 'month', 'day', 'hours'])
    df_aligned = df_encoded.reindex(columns=training_columns, fill_value=0)

    return df_aligned.iloc[0].to_dict()

def estimate_delay(weather_data, bst, num_points):
    """
    Estimates the delay based on weather data and the number of route points.

    Args:
    - weather_data (dict): Weather data for a particular route point.
    - bst (XGBoost model): Pre-trained XGBoost model for delay prediction.
    - num_points (int): Total number of route points.

    Returns:
    - timedelta: Estimated delay duration.
    """
    # Create input vector for the model
    input_vector = create_input_vector(weather_data)

    # Convert input vector to DMatrix and predict delay
    dmatrix = xgb.DMatrix(input_vector)
    predicted_delay = bst.predict(dmatrix)[0]  # Scalar delay prediction

    # Ensure non-negative delay
    predicted_delay = max(predicted_delay, 0)

    # Convert predicted delay to timedelta
    delay = timedelta(minutes=float(predicted_delay))

    # Adjust delay based on the number of route points
    adjusted_delay = delay / (num_points)

    return adjusted_delay

@time_logger
def calculate_delays(source, destination, departure_date, departure_time):
    """
    Calculates the total delay for a flight from source to destination.

    Args:
    - source (str): ICAO code of the source airport.
    - destination (str): ICAO code of the destination airport.
    - departure_date (str): Departure date in 'YYYY-MM-DD' format.
    - departure_time (str): Departure time in 'HH:MM:SS' format.

    Returns:
    - timedelta: Total estimated delay.
    """
    # Convert airport codes to ICAO and get route points and cruise speed
    source_icao, destination_icao = convert_to_icao(source), convert_to_icao(destination)
    route_points, cruise_speed_kts = calculate_route_points(source_icao, destination_icao)

    # Initialize variables for delay calculation
    total_delay = timedelta(0)
    expected_arrival = datetime.strptime(f'{departure_date} {departure_time}', '%Y-%m-%d %H:%M:%S')
    avg_speed_kmh = cruise_speed_kts * 1.852  # Convert knots to km/h
    last_point = (source_icao, "Departure Airport", *route_points[0][2:])

    num_points = len(route_points)
    training_columns = list(pd.read_csv('data/training.csv').columns)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start the NLP delay estimation in a separate thread
        future_delay_nlp = executor.submit(estimate_delay_nlp, source, destination, departure_date)

        # Iterate over route points concurrently
        for point in route_points:
            ident, name, lat, lon = point

            # Calculate distance and travel time to the next point
            distance = haversine(last_point[2], last_point[3], lat, lon)
            travel_time = timedelta(hours=distance / avg_speed_kmh)
            expected_arrival += total_delay + travel_time

            # Fetch and prepare weather data for model prediction
            weather_data = fetch_weather_data(lat, lon, expected_arrival)
            weather_data = add_dep_time_to_weather_data(weather_data, expected_arrival, training_columns)
            weather_data['distance'] = distance / 1.61  # Convert miles to kilometers

            # Estimate delay at current route point
            delay = estimate_delay(weather_data, bst, num_points)
            total_delay += delay

            last_point = point
            #print(f"Expected arrival at {name} ({ident}): {expected_arrival} with a delay of {delay}")
            #print('\n\n')

        # Retrieve the NLP delay result
        delay_nlp = future_delay_nlp.result()

    return ((total_delay * 0.9) + (0.1 * delay_nlp))