from django.db import models
from django.contrib.postgres.search import SearchVectorField

class Publication(models.Model):
    client_id = models.CharField(max_length=1024)
    title = models.CharField(max_length=2048)
    description = models.TextField()
    fulltext = models.TextField()
    license = models.CharField(max_length=1024)
    url = models.CharField(max_length=2048)
    raw_data = models.TextField()
    language = models.CharField(max_length=512)
    source = models.CharField(max_length=1024)
    partner = models.CharField(max_length=1024)
    search_vector = SearchVectorField(default='')
