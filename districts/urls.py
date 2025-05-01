from django.urls import path, include

from .views import BestDistrictsView

urlpatterns = [
    path('districts/best-districts/', BestDistrictsView.as_view(), name='best_districts'),
]