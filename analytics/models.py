from django.db import models
from django.conf import settings


class CsvUpload(models.Model):
    """Tracks CSV file uploads for royalty statements."""
    UPLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('completed_with_errors', 'Completed with Errors'),
    ]

    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='csv_uploads')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=UPLOAD_STATUS_CHOICES, default='pending')  # Changed to 25
    processed_rows = models.IntegerField(default=0)
    total_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"CSV Upload: {self.filename} by {self.artist.username} ({self.status})"

    def update_stats(self, success_count=0, error_count=0):
        """Helper method to update processing statistics."""
        self.success_count += success_count
        self.error_count += error_count
        self.processed_rows = self.success_count + self.error_count

        if self.processed_rows >= self.total_rows:
            self.status = 'completed' if self.error_count == 0 else 'completed_with_errors'
        self.save()


class Platform(models.Model):
    name = models.CharField(max_length=200, unique=True)
    api_name = models.CharField(max_length=200, unique=True)
    base_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Album(models.Model):
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='albums')
    title = models.CharField(max_length=255)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['artist', 'title']
        ordering = ['-release_date', 'title']

    def __str__(self):
        return f"{self.title} by {self.artist.username}"


class Track(models.Model):
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tracks')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='tracks', null=True, blank=True)
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    track_number = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['artist', 'name']
        ordering = ['album', 'track_number', 'name']

    def __str__(self):
        return f"{self.name} by {self.artist.username}"


class RoyaltyStatement(models.Model):
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='royalty_statements')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='royalty_statements')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='royalty_statements')
    upload = models.ForeignKey(CsvUpload, on_delete=models.CASCADE, related_name='statements', null=True,
                               blank=True)  # NEW FIELD
    period_start = models.DateField()
    period_end = models.DateField()
    streams = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=4, default=0.0)
    currency = models.CharField(max_length=3, default='USD')
    source_row_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_end', 'platform']
        indexes = [
            models.Index(fields=['artist', 'period_end']),
            models.Index(fields=['platform', 'period_end']),
        ]

    def __str__(self):
        return f"Royalty: {self.track.name} on {self.platform.name} ({self.period_end})"

    def save(self, *args, **kwargs):
        import hashlib
        if not self.pk:
            source_string = f"{self.artist}-{self.track}-{self.platform}-{self.period_end}-{self.streams}-{self.revenue}-{self.currency}"
            self.source_row_hash = hashlib.sha256(source_string.encode()).hexdigest()
        super().save(*args, **kwargs)