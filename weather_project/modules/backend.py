import requests
import json
import os
from functools import lru_cache
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from dotenv import load_dotenv, dotenv_values

load_dotenv()

cache = {}
CACHE_DURATION = timedelta(hours=24)


def get_api(location):
    """Gets weather data from api"""
    api_key = os.getenv("API_KEY")
    response = requests.request("GET",
                                f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/next7days?unitGroup=metric&elements=datetime%2Ctemp%2Chumidity%2Cuvindex&key=3D56DREY2VT2XMY6UXKFQN4Y9&contentType=json")

    if response.status_code != 200:
        print('Unexpected Status code: ', response.status_code)
        return "error"

    jsonData = response.json()
    print(jsonData)
    return jsonData


def filter_api(weather_data):
    filtered_data = []
    data = weather_data['days']

    for days in data:
        date = days['datetime']
        morning_temp = days['hours'][8]['temp']
        morning_humidity = days['hours'][8]['humidity']
        night_temp = days['hours'][20]['temp']
        night_humidity = days['hours'][20]['humidity']

        max_uv_index = 0
        max_uv_hour = None
        for hour in days['hours']:
            if hour['uvindex'] > max_uv_index:
                max_uv_index = hour['uvindex']
                max_uv_hour = hour['datetime']

        all_days = {
            'date': date,
            'morning_temp': morning_temp,
            'morning_humidity': morning_humidity,
            'night_temp': night_temp,
            'night_humidity': night_humidity,
            'max_uv_index': max_uv_index,
            'max_uv_hour': max_uv_hour
        }

        filtered_data.append(all_days)
    # print(filtered_data)
    return filtered_data


def create_json_file(filtered_data):
    """Return json file with weather filter"""
    file = "data/json_data"
    with open(file, 'w') as file:
        json.dump(filtered_data, file)
    return file


def read_json_file():
    with open("data/json_data", "r") as file:
        data = json.load(file)

    return data


def get_or_cache_filtered_data(location):
    """Get or cache filtered weather data."""
    # Check if cached data exists
    if location in cache:
        cached_data, timestamp = cache[location]
        # Check if cached entry is still valid
        if datetime.now() - timestamp < CACHE_DURATION:
            print("Returning cached filtered data for:", location)
            return cached_data

    # Get raw data if no valid cached data exists
    raw_weather_data = get_api(location)

    if raw_weather_data == "error":
        return "error"

    # Filter the raw weather data
    filtered_data = filter_api(raw_weather_data)

    # Cache the filtered data with the current timestamp
    cache[location] = (filtered_data, datetime.now())

    return filtered_data
