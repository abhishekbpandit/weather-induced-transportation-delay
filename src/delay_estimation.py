from datetime import datetime, timedelta
from util.util import convert_to_icao, haversine, create_input_vector, first_element
from .delay_nlp import estimate_delay_nlp
from .route import calculate_route_points
from .weather_data import fetch_weather_data

import joblib
import xgboost as xgb
import pandas as pd


bst = joblib.load('models/my_xgboost.pkl')

def add_dep_time_to_weather_data(weather_data, departure_time, training_columns):
    """
    Adds the departure time to the weather data.

    Args:
    weather_data (dict): Weather data at a certain time.
    departure_time (datetime): Time when the weather data was calculated

    Returns:
    dict: Updated weather data including departure time.
    """
    # Convert departure time to minutes since midnight, which is a common way to encode time for models
    
    
    # Update the weather_data dictionary
    weather_data['hours'] = departure_time.hour
    weather_data['minutes'] = departure_time.minute
    weather_data['day'] = departure_time.day
    weather_data['month'] = departure_time.month

    if isinstance(weather_data['preciptype'], list) and len(weather_data['preciptype']) > 0:
        weather_data['preciptype'] = weather_data['preciptype'][0]
    
    if 'stations' in weather_data:
        del weather_data['stations']
    df = pd.DataFrame(weather_data, index=[0])

    # Apply this function to your categorical columns if they contain lists
    for col in ['preciptype', 'icon', 'month', 'day', 'hours']:
        if col in df.columns:
            df[col] = df[col].apply(first_element).astype('category')

    # One-hot encode categorical variables
    df_encoded = pd.get_dummies(df, columns=['preciptype', 'icon', 'month', 'day', 'hours'])

    # Reindex with training columns, filling missing with 0s
    df_aligned = df_encoded.reindex(columns=training_columns, fill_value=0)


    return df_aligned.to_dict()

def estimate_delay(weather_data, bst, num_points):
    # Create the input vector for the model
    input_vector = create_input_vector(weather_data)

    # Convert input vector to DMatrix
    dmatrix = xgb.DMatrix(input_vector)
    
    # Use the model to predict the delay
    predicted_delay = bst.predict(dmatrix)[0] # Get the scalar delay prediction
    
    if predicted_delay < 0:
        predicted_delay = 0
    
    # Here we assume that predicted_delay is in minutes
    delay = timedelta(minutes=float(predicted_delay))
    
    # Adjust the delay as per the number of route points
    adjusted_delay = delay / (num_points * num_points)

    return adjusted_delay

def calculate_delays(source, destination, departure_date, departure_time):
    source_icao = convert_to_icao(source)
    destination_icao = convert_to_icao(destination)
    route_points, cruise_speed_kts = calculate_route_points(source_icao, destination_icao)
    total_delay = timedelta(0)
    expected_arrival = datetime.strptime(f'{departure_date} {departure_time}', '%Y-%m-%d %H:%M:%S')

    # Convert cruise speed to km/h (1 knot ≈ 1.852 km/h)
    avg_speed_kmh = cruise_speed_kts * 1.852

    last_point = (source_icao, "Departure Airport", *route_points[0][2:])

    num_points = len(route_points)
    training_columns = list(pd.read_csv('data/training.csv').columns)


    delay_nlp = estimate_delay_nlp(source, destination, departure_date)

    for point in route_points:
        ident, name, lat, lon = point
        distance = haversine(last_point[2], last_point[3], lat, lon)
        travel_time = timedelta(hours=distance / avg_speed_kmh)
        expected_arrival = expected_arrival + total_delay + travel_time
        weather_data = fetch_weather_data(lat, lon, expected_arrival)

        weather_data = add_dep_time_to_weather_data(weather_data, expected_arrival, training_columns)
        weather_data['distance'] = distance/1.61

        delay = estimate_delay(weather_data, bst, num_points)
        total_delay += delay
        last_point = point
        print(f"Expected arrival at {name} ({ident}): {expected_arrival} with a delay of {delay}")
        print('\n\n')

    return ((total_delay * 0.7) + (0.3 * delay_nlp))
