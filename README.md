# District Recommender

A Django REST API that recommends the best districts in Bangladesh to visit based on weather and air quality, and provides travel recommendations between locations. The project uses Celery for background tasks and Redis for caching.

## Features

- **Best Districts API**: Returns the top 10 districts with the best weather and air quality.
- **Travel Recommender API**: Compares your current location and a destination for a given date, recommending whether to travel.
- **Automated Caching**: Uses Celery and django-celery-beat to periodically update cached district data.
- **Dockerized**: Easily run with Docker and Docker Compose.

## Requirements

- Docker & Docker Compose (recommended)
- Or: Python 3.12+, pip, Redis server

## Setup (with Docker)

1. **Clone the repository**  
   ```sh
   git clone <repo-url>
   cd best_district_recommender
   ```

2. **Build and start the services**  
   ```sh
   docker-compose up --build
   ```

3. The API will be available at [http://localhost:8000/api/](http://localhost:8000/api/).

## API Endpoints

### 1. Get Best Districts

- **URL**: `/api/districts/best-districts/`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "districts": [
      {
        "district": "District Name",
        "avg_temp_at_2pm": 30.5,
        "avg_pm25": 12.3
      },
      ...
    ]
  }
  ```

### 2. Travel Recommender

- **URL**: `/api/districts/recommender/`
- **Method**: `GET`
- **Body (JSON)**:
  ```json
  {
    "latitude": 23.8103,
    "longitude": 90.4125,
    "destination": "Dhaka",
    "travel_date": "2024-07-01"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Your destination is 2.5°C cooler and has significantly better air quality. Enjoy your trip!"
  }
  ```

## Development (without Docker)

1. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   ```

2. **Run Redis**  
   Make sure Redis is running on `localhost:6379`.

3. **Apply migrations and collect static files**  
   ```sh
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Start Django server**  
   ```sh
   python manage.py runserver
   ```

5. **Start Celery worker and beat**  
   In separate terminals:
   ```sh
   celery -A district_recommender worker --loglevel=info
   celery -A district_recommender beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

## Redis Host Configuration

If you are running Redis **locally** (not in Docker), update your `district_recommender/settings.py` as follows:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379/1"
    },
}

CELERY_BROKER_URL = "redis://localhost:6379/0"
```

If you are using **Docker Compose**, keep the default:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://redis:6379/1"
    },
}

CELERY_BROKER_URL = "redis://redis:6379/0"
```

## Project Structure

- [`district_recommender/`](district_recommender/) - Django project settings and Celery config
- [`districts/`](districts/) - Main app with API views, tasks, serializers, and utils
- [`Dockerfile`](Dockerfile) & [`docker-compose.yml`](docker-compose.yml) - Containerization setup

## License

MIT License
