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
            return Response(
                {"districts": cached_data[:10]}, status=status.HTTP_200_OK
            )
        else:
            # Fetch the data from the URL
            district_response = requests.get(DISTRICT_URL)
            results = []
            if district_response.status_code == 200:
                districts_data = district_response.json()["districts"]
                for district in districts_data:
                    # Fetch weather data for each district
                    lat, lon = district["lat"], district["long"]
                    name = district["name"]

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

                    # Fetch air quality data for each district
                    air_quality_response = requests.get(
                        AIR_QUALITY_URL,
                        params={
                            "latitude": district["lat"],
                            "longitude": district["long"],
                            "current_weather": True,
                            "hourly": "pm2_5",
                            "timezone": "Asia/Dhaka",
                        },
                    )
                    if air_quality_response.status_code == 200:
                        air_quality_data = air_quality_response.json()
                        daily_aq_chunked_data = []
                        hourly_data = air_quality_data["hourly"]["pm2_5"]
                        for i in range(0, len(hourly_data), 24):
                            chunk = hourly_data[i : i + 24]
                            daily_aq_chunked_data.append(chunk)

                        total_pm_at_2pm = 0
                        for day in daily_aq_chunked_data:
                            total_pm_at_2pm += day[14]
                        average_pm = round(
                            total_pm_at_2pm / len(daily_aq_chunked_data), 2
                        )
                        district["air_quality"] = {
                            "7_days_average_pm2_5_at_2pm": total_pm_at_2pm,
                        }
                        results.append(
                            {
                                "district": name,
                                "avg_temp_at_2pm": round(average_temperature, 2),
                                "avg_pm25": round(average_pm, 2),
                            }
                        )
                    sorted_results = sorted(
                        results,
                        key=lambda result: (
                            result["avg_temp_at_2pm"],
                            result["avg_pm25"],
                        ),
                    )
                cache.set(
                    "districts_data",
                    sorted_results,
                    timeout=60 * 60,  # Cache for 1 hour
                )
                # Return the top 10 districts based on the criteria
                return Response(
                    {"districts": sorted_results[:10]},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {"error": "Failed to fetch district data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
