from django.db import models
from django.utils import timezone

class Dataset(models.Model):
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    summary_json = models.JSONField()
    preview_csv = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.created_at:%Y-%m-%d %H:%M})"
