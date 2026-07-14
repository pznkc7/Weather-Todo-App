from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

LOCATION_CACHE_LIFETIME = timedelta(hours=6)


class UserLocation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cached_location',
    )

    city_name = models.CharField(max_length=120, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} @ {self.city_name or f"{self.latitude},{self.longitude}"}'

    @property
    def is_stale(self):
        return timezone.now() - self.updated_at > LOCATION_CACHE_LIFETIME