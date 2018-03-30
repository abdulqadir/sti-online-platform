from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex

class Store(models.Model):
    client_id = models.CharField(max_length=1024, null=True)
    title = models.CharField(max_length=2048, blank=True)
    description = models.TextField(blank=True, null=True)
    license = models.CharField(max_length=1024, null=True)
    url = models.CharField(max_length=2048, null=True)
    raw_data = models.TextField()
    meta_data = JSONField(null=True)
    language = models.CharField(max_length=512, null=True)
    partner = models.CharField(max_length=1024)
    store_type = models.CharField(max_length=1024)
    keywords = models.TextField(null=True)
    location = models.CharField(max_length=1024, null=True)
    search_vector = SearchVectorField(default='')
    last_updated = models.DateField(auto_now=True)

    class Meta:
        indexes = [
                GinIndex(fields=['search_vector']),
                models.Index(fields=['language']),
                models.Index(fields=['partner']),
                models.Index(fields=['store_type']),
            ]

class Event(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ' ' + self.title
