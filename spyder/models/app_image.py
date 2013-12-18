# -*- coding:utf-8 -*-
from django.db import models


class AppImage(models.Model):
    application = models.ForeignKey('spyder.Application')
    image = models.ImageField(max_length=255, upload_to='app_images/', blank=True)

    class Meta:
        app_label = 'spyder'