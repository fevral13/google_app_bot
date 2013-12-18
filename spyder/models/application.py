# -*- coding:utf-8 -*-
from django.db import models


class Application(models.Model):
    app_id = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    icon = models.ImageField(max_length=255, upload_to='app_images/', blank=True)
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    downloads = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = 'spyder'