# weather-induced-transportation-delay

## Methodology

## Overview
This project aims to predict flight delays by combining machine learning and natural language processing techniques. It uses a Streamlit app for user input, processes flight route data, analyzes weather conditions at each route point, and utilizes news articles to estimate delays.

### Steps
* **1. Streamlit App Interface**
  * Built a Streamlit app to collect user inputs: source, destination, date, and time of travel.
* **2. ICAO Code Conversion**
  * Converted the source and destination airports to ICAO format using a CSV file containing IATA and ICAO codes.
* **3. Flight Plan Retrieval**
  * Used the FlightPlanDatabase API to obtain flight plans for the given source, destination, and datetime combination.
* **4. Route Point Extraction**
  * Extracted all route points using the plan id from FlightPlanDatabase API.
* **5. Weather Data Collection**
  * At each route point, gathered weather data using the Visual Crossing API.
**6. Delay Calculation via ML Model**
  * Calculated potential delays at each route point based on weather data using a pre-trained machine learning model.
  * Adjusted the delay estimate by dividing it by the number of route points.
  * Summed up the delay from all points and took half of this sum as part of the total delay estimate.
* **7. NLP Pipeline for Delay Prediction**
  * Queried Google News API to gather news articles about flight delays specific to the source-destination pair and relevant dates.
  * Filtered news articles to those relevant to the travel date.
  * Processed these articles through a Mistral model hosted on GCP using ngrok to extract delay information.
  * Calculated the mean delay value from all articles.
* **8. Total Delay Estimation**
  * The total delay estimate was calculated as 70% of the delay predicted by the ML model and 30% of the delay extracted from the NLP pipeline.

## ML Model Training
* Used a dataset containing flight details and delay variables.
* Selected a sample of 10,000 rows, including 1,000 rows with weather_delay greater than 0.
* Extracted latitude and longitude for each row.
* Collected weather data for these points using the Visual Crossing API.
* Trained an XGBoost model on this data to predict delays.

## Technologies Used
* Streamlit
* FlightPlanDatabase API
* Visual Crossing API
* Google News API
* XGBoost
* Mistral AI model
* NGrok
