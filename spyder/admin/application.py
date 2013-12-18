# -*- coding:utf-8 -*-
from django.contrib import admin
from spyder.models import AppImage, Application


class AppImageInline(admin.TabularInline):
    model = AppImage


class ApplicationAdmin(admin.ModelAdmin):
    inlines = (AppImageInline, )
    list_display = ('app_id', 'name', 'icon_image', 'rating', 'downloads')
    search_fields = ('app_id', 'name')

    def icon_image(self, obj):
        return '<img width="60px" src="%s">' % obj.icon.url
    icon_image.allow_tags = True

admin.site.register(Application, ApplicationAdmin)

