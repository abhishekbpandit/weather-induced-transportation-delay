import pandas as pd
import pickle

def create_airport_dict(csv_path):
    df = pd.read_csv(csv_path)
    airport_dict = {f"{row['airport']} ({row['iata']})": row['iata'] for _, row in df.iterrows()}
    return airport_dict

def save_airport_dict(airport_dict, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(airport_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Path to your CSV file
csv_path = 'data/iata-icao.csv'
airport_dict = create_airport_dict(csv_path)

# Save the dictionary to a file
save_airport_dict(airport_dict, 'data/airport_dict.pkl')
