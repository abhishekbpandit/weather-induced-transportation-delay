from src import calculate_delays
from util import load_airport_dict
import datetime
import streamlit as st

import warnings
warnings.filterwarnings('ignore')

# Load airport dict from pkl
airport_dict = load_airport_dict('data/airport_dict.pkl')

# Create lists for dropdowns (sorted alphabetically)
airport_list = sorted(airport_dict.keys())

st.title('Weather-Induced Delays in Transportation Routes')

# User Inputs
st.sidebar.header('User Input Features')
date = st.sidebar.date_input("Select Departure Date", datetime.date.today())
time = st.sidebar.time_input('Select Departure Time (EST)',  value="now", step=300)

# Dropdown for source airport
source_airport_name = st.sidebar.selectbox('Select Source Airport', airport_list)
source_airport_iata = airport_dict[source_airport_name]

# Dropdown for destination airport
destination_airport_name = st.sidebar.selectbox('Select Destination Airport', airport_list)
destination_airport_iata = airport_dict[destination_airport_name]

# Submit button
if st.sidebar.button('Submit'):
    # Check if source and destination are not the same
    if source_airport_iata == destination_airport_iata:
        st.error("Source and destination airports cannot be the same.")
    else:
        # Display User Selections
        st.write(f"Date Selected: {date}")
        st.write(f"Time Selected: {time}")
        st.write(f"Route: {source_airport_iata} to {destination_airport_iata}")

        # Placeholder for Estimated Delay - To be updated with actual data
        estimated_delay = calculate_delays(source_airport_iata, destination_airport_iata, date, time)
        st.write(f"Estimated Delay: {estimated_delay}")
