import requests
from django.core.cache import cache
from celery import shared_task

DISTRICT_URL = "https://raw.githubusercontent.com/strativ-dev/technical-screening-test/main/bd-districts.json"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


@shared_task
def update_best_districts_cache():
    try:
        print("🔄 Updating best districts cache...")
        district_response = requests.get(DISTRICT_URL)

        districts_data = district_response.json()["districts"]
        results = []
        for district in districts_data:
            lat, lon = district["lat"], district["long"]
            name = district["name"]

            avg_temp = get_average_temperature(lat, lon)
            avg_pm = get_average_pm(lat, lon)

            results.append(
                {
                    "district": name,
                    "avg_temp_at_2pm": round(avg_temp, 2),
                    "avg_pm25": round(avg_pm, 2),
                }
            )

        results.sort(key=lambda d: (d["avg_temp_at_2pm"], d["avg_pm25"]))
        cache.set("best_districts", results, timeout=3600)
        print("✅ Cached top districts updated.")
    except Exception as e:
        print(f"❌ Failed to update cache: {e}")


def get_average_pm(lat, lon):
    try:
        air_quality_response = requests.get(
            AIR_QUALITY_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "hourly": "pm2_5",
                "timezone": "Asia/Dhaka",
            },
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching air quality data: {e}")
        return None
    if air_quality_response.status_code != 200:
        print(f"Error fetching air quality data: {air_quality_response.status_code}")
        return None
    
    air_quality_data = air_quality_response.json()
    daily_aq_chunked_data = []
    hourly_data = air_quality_data["hourly"]["pm2_5"]
    for i in range(0, len(hourly_data), 24):
        chunk = hourly_data[i : i + 24]
        daily_aq_chunked_data.append(chunk)

    total_pm_at_2pm = 0
    for day in daily_aq_chunked_data:
        total_pm_at_2pm += day[14]
    average_pm = round(total_pm_at_2pm / len(daily_aq_chunked_data), 2)

    return average_pm


def get_average_temperature(lat, lon):
    try:
        weather_response = requests.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m",
                "timezone": "Asia/Dhaka",
                "current_weather": True,
            },
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
    if weather_response.status_code != 200:
        print(f"Error fetching weather data: {weather_response.status_code}")
        return None
    
    daily_weather_chunked_data = []
    weather_data = weather_response.json()
    hourly_data = weather_data["hourly"]["temperature_2m"]
    for i in range(0, len(hourly_data), 24):
        chunk = hourly_data[i : i + 24]
        daily_weather_chunked_data.append(chunk)

    total_temperature_at_2pm = 0
    for day in daily_weather_chunked_data:
        total_temperature_at_2pm += day[14]
    average_temperature = round(
        total_temperature_at_2pm / len(daily_weather_chunked_data),
        2,
    )

    return average_temperature