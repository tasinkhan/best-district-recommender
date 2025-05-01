from rest_framework import serializers
import datetime


class RecommenderSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    destination = serializers.CharField(max_length=100)
    travel_date = serializers.DateField()

    def validate(self, data):
        """
        Validate the input data.
        """
        if not self.is_valid_district(data["destination"]):
            raise serializers.ValidationError("Invalid district name.")

        if data["travel_date"] < datetime.date.today():
            raise serializers.ValidationError("Travel date must be in the future.")

        return data
