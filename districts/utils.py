import requests
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_weather_and_air(lat, lon, date):
    try:
        weather_response = requests.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m",
                "timezone": "Asia/Dhaka",
                "start_date": date,
                "end_date": date,
            },
        )
        air_quality_response = requests.get(
            AIR_QUALITY_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "pm2_5",
                "timezone": "Asia/Dhaka",
                "start_date": date,
                "end_date": date,
            },
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, None

    if weather_response.status_code != 200 or air_quality_response.status_code != 200:
        print(
            f"Error fetching data: {weather_response.status_code}, {air_quality_response.status_code}"
        )
        return None, None

    weather_data = weather_response.json()
    temperature_at_2pm = weather_data["hourly"]["temperature_2m"][14]
    air_quality_data = air_quality_response.json()
    pm_at_2pm = air_quality_data["hourly"]["pm2_5"][14]
    return temperature_at_2pm, pm_at_2pm
