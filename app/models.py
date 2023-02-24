from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class GNL(models.Model):
    logo = models.ImageField(null = True, blank = True)
    text = models.TextField(null=True, blank = True)
    close = models.FloatField(null=True,blank=True)
    change = models.FloatField(null=True,blank=True)
    percent = models.FloatField(null=True,blank=True)
    volume = models.FloatField(null=True,blank=True)
    date = models.DateTimeField(null=True,blank=True)
