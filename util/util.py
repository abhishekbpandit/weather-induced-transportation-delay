from math import radians, cos, sin, asin, sqrt
import pandas as pd
import pickle
import time

def time_logger(func):
    """
    Decorator that prints the time taken by a function to run.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function {func.__name__} took {elapsed_time:.2f} seconds to run.")
        return result
    return wrapper

# Helper function to extract the first element from a list
def first_element(list_like):
    if isinstance(list_like, list) and len(list_like) > 0:
        return list_like[0]
    return list_like

# Function to load the airport dictionary
def load_airport_dict(filename):
    with open(filename, 'rb') as handle:
        return pickle.load(handle)

def convert_to_icao(airport_code):
    df = pd.read_csv('data/iata-icao.csv')
    return df[df['iata'] == airport_code]['icao'].iloc[0]

def get_lat_lon_from_iata(airport_codes):
    df = pd.read_csv('data/iata-icao.csv')
    code_to_loc = {}
    for code in airport_codes:
        lat, lon = df[df['iata'] == code]['latitude'], df[df['iata'] == code]['longitude']
        if code not in code_to_loc:
            code_to_loc[code] = (lat, lon)
    return code_to_loc

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def create_input_vector(weather_data):
    # Convert weather_data dict to DataFrame with the same structure used during training
    # The column names and order must match the training data
    df = pd.DataFrame([weather_data], columns=list(pd.read_csv('data/training.csv').columns))
    
    # Handle categorical variables if your model expects them as one-hot encoded
    # Assuming you have a function to one-hot encode the categorical features if needed
    
    # Fill missing values or handle them as needed
    df.fillna(-999, inplace=True)
    
    # Convert all columns to numeric
    df = df.apply(pd.to_numeric, errors='coerce')
    
    return df
