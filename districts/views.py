import httpx
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from datetime import datetime
from .serializers import RecommenderSerializer
from .utils import fetch_weather_and_air
from asyncio import gather

DISTRICT_URL = "https://raw.githubusercontent.com/strativ-dev/technical-screening-test/main/bd-districts.json"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class BestDistrictsView(APIView):
    def get(self, request):
        best_districts_cached_data = cache.get("best_districts")
        if best_districts_cached_data:
            return Response(
                {"districts": best_districts_cached_data[:10]},
                status=status.HTTP_200_OK,
            )

        districts_data = get_district_data()
        if not districts_data:
            return Response({"error": "Failed to fetch district data"}, status=500)
        results = []
        for district in districts_data:
            lat, lon = district["lat"], district["long"]
            name = district["name"]

            avg_temp = self.get_average_temperature(lat, lon)
            avg_pm = self.get_average_pm(lat, lon)
            if avg_temp is None or avg_pm is None:
                return Response(
                    {"error": "Failed to fetch weather or air quality data"}, status=500
                )

            results.append(
                {
                    "district": name,
                    "avg_temp_at_2pm": round(avg_temp, 2),
                    "avg_pm25": round(avg_pm, 2),
                }
            )

        results.sort(key=lambda d: (d["avg_temp_at_2pm"], d["avg_pm25"]))
        cache.set("best_districts", results, timeout=3600)
        return Response({"districts": results[:10]}, status=200)

    def get_average_pm(self, lat, lon):
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
            print(
                f"Error fetching air quality data: {air_quality_response.status_code}"
            )
            return None

        air_quality_data = air_quality_response.json()
        daily_aq_chunked_data = []
        hourly_data = air_quality_data["hourly"]["pm2_5"]
        for i in range(0, len(hourly_data), 24):
            chunk = hourly_data[i : i + 24]
            daily_aq_chunked_data.append(chunk)

        total_pm_at_2pm = 0
        for day in daily_aq_chunked_data:
            value = day[14]
            if value is not None:
                total_pm_at_2pm += value
        average_pm = round(total_pm_at_2pm / len(daily_aq_chunked_data), 2)

        return average_pm

    def get_average_temperature(self, lat, lon):
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


def get_district_data():
    district_data = cache.get("district_data")
    if district_data:
        return district_data
    else:
        try:
            response = requests.get(DISTRICT_URL, timeout=1000)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching district data: {e}")
            return None
        if response.status_code != 200:
            print(f"Error fetching district data: {response.status_code}")
            return None
        district_data = response.json()["districts"]
        cache.set("district_data", district_data, timeout=3600)
        return district_data


class TravelRecommenderView(APIView):

    def get(self, request):
        serializer = RecommenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        current_location_lat = data["latitude"]
        current_location_lon = data["longitude"]
        date = data["travel_date"]
        destination = data["destination"]

        district_data = cache.get("district_data")
        if not district_data:
            district_data = get_district_data()
            if not district_data:
                return Response({"error": "Failed to fetch district data"}, status=500)

        for district in district_data:
            if district["name"] == destination:
                destination_location_lat = district["lat"]
                destination_location_lon = district["long"]
                break
        else:
            return Response({"error": "Invalid destination"}, status=400)

        current_location_temp, current_location_pm = fetch_weather_and_air(
            current_location_lat, current_location_lon, date
        )
        if current_location_temp is None or current_location_pm is None:
            return Response(
                {"error": "Failed to fetch weather or air quality data"}, status=500
            )
        destination_location_temp, destination_location_pm = fetch_weather_and_air(
            destination_location_lat, destination_location_lon, date
        )
        if destination_location_temp is None or destination_location_pm is None:
            return Response(
                {"error": "Failed to fetch weather or air quality data"}, status=500
            )
        temperature_difference = round(
            (current_location_temp - destination_location_temp), 2
        )
        if (
            current_location_temp < destination_location_temp
            and current_location_pm < destination_location_pm
        ):
            return Response(
                {
                    "message": f"Your {destination} is hotter and has worse air quality than your current location. It’s better to stay where you are."
                },
                status=200,
            )
        elif (
            current_location_temp > destination_location_temp
            and current_location_pm > destination_location_pm
        ):
            return Response(
                {
                    "message": f"Your destination is {temperature_difference}°C cooler and has significantly better air quality. Enjoy your trip!"
                },
                status=200,
            )
        else:
            return Response(
                {
                    "message": "Both locations have similar weather and air quality. Enjoy your trip!"
                },
                status=200,
            )
