from django.db import models
from django.contrib.postgres.fields import JSONField

class Metadata(models.Model):
    partner = models.CharField(max_length=128, unique=True)
    keyval = JSONField()
