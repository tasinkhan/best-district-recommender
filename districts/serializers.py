from rest_framework import serializers
import datetime


class RecommenderSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    destination = serializers.CharField(max_length=100, required=True)
    travel_date = serializers.DateField(required=True, input_formats=["%Y-%m-%d"], format="%Y-%m-%d")

    def validate_travel_date(self, value):
        """
        Field-level validation for travel_date:
        ensures it’s strictly _after_ today.
        """
        today = datetime.date.today()
        if value <= today:
            # this attaches the error *to* 'travel_date'
            raise serializers.ValidationError("Travel date must be in the future.")
        return value
