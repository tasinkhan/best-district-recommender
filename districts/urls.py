from django.urls import path, include

from .views import BestDistrictsView, TravelRecommenderView

urlpatterns = [
    path('districts/best-districts/', BestDistrictsView.as_view(), name='best_districts'),
    path('districts/recommender/', TravelRecommenderView.as_view(), name='travel_recommender'),
]