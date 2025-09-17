from django.db import models
from django.conf import settings

class PlatformInsight(models.Model):
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='platform_insights')
    platform = models.CharField(max_length=50)
    track_name = models.CharField(max_length=255)
    insight_type = models.CharField(max_length=50)
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['artist', 'platform', 'insight_type']),
        ]
        ordering = ['-timestamp', 'platform']

    def __str__(self):
        return f"{self.artist.username} - {self.platform} - {self.track_name} - {self.insight_type}"