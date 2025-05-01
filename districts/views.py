import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from datetime import datetime

DISTRICT_URL = "https://raw.githubusercontent.com/strativ-dev/technical-screening-test/main/bd-districts.json"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class BestDistrictsView(APIView):
    def get(self, request):
        # Check if the data is already cached
        cached_data = cache.get("districts_data")
        if cached_data:
            districts_data = cached_data
        else:
            # Fetch the data from the URL
            response = requests.get(DISTRICT_URL)
            if response.status_code == 200:
                districts_data = response.json()["districts"]
                for district in districts_data:
                    # Fetch weather data for each district
                    lat, lon = district["lat"], district["long"]

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
                    if weather_response.status_code == 200:
                        daily_chunked_data = []
                        weather_data = weather_response.json()
                        hourly_data = weather_data["hourly"]["temperature_2m"]
                        for i in range(0, len(hourly_data), 24):
                            chunk = hourly_data[i : i + 24]
                            daily_chunked_data.append(chunk)

                        total_temperature_at_2pm = 0
                        for day in daily_chunked_data:
                            total_temperature_at_2pm += day[14]
                        average_temperature = round(total_temperature_at_2pm / len(daily_chunked_data), 2)
                        district["weather"] = {
                            "7_days_average_temperature_at_2pm": average_temperature,
                            "current_weather": weather_data["current_weather"],
                        }
                    else:
                        district["weather"] = {}
                return Response(
                    {"districts": districts_data},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {"error": "Failed to fetch district data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
