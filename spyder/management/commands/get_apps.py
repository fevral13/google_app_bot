# -*- coding:utf-8 -*-
from decimal import Decimal
import time
from urllib import quote
import urllib
import random
import hashlib
# from multiprocessing import Process, Queue, Lock
from threading import Thread, Lock
from Queue import Queue

from django.conf import settings
import os
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException

from spyder.models import Application, AppImage


_stop = object()

from django.core.management import BaseCommand

app_queue = Queue()
image_queue = Queue()
db_lock = Lock()


class ImageWorker(Thread):
    def __init__(self, *args, **kwargs):
        super(ImageWorker, self).__init__(*args, **kwargs)
        self.running = True
        print('ImageThread %s started' % self.name)

    def run(self):

        while self.running:
            task = image_queue.get()

            if task is _stop:
                image_queue.put(task)
                self.running = False
            else:
                url, app = task
                print('%s: %s' % (self.name, url))

                image = AppImage()
                image.application = app
                image_name = hashlib.md5(str(random.randint(1, 9999999))).hexdigest() + '.jpg'

                with open(os.path.join(settings.MEDIA_ROOT, 'app_images', image_name), 'wb') as f:
                    f.write(urllib.urlopen(url).read())
                image.image = os.path.join('app_images', image_name)
                with db_lock:
                    image.save()


class AppWorker(Thread):
    def __init__(self, *args, **kwargs):
        super(AppWorker, self).__init__(*args, **kwargs)
        self.wd = webdriver.Firefox()
        self.running = True
        print('AppThread %s started' % self.name)

    def run(self):

        while self.running:
            app_id = app_queue.get()

            if app_id is _stop:
                app_queue.put(app_id)
                self.running = False
                self.wd.close()

            if not Application.objects.filter(app_id=app_id).exists():
                print('%s: %s' % (self.name, app_id))
                app = Application()
                app.app_id = app_id
                self.wd.get('https://play.google.com/store/apps/details?id=%s' % app_id)

                app.name = self.wd.find_element_by_css_selector('div.document-title div').text
                app_icon_url = self.wd.find_element_by_css_selector('div.details-info .cover-container img.cover-image').get_attribute('src')
                image_name = hashlib.md5(str(random.randint(1, 9999999))).hexdigest() + '.jpg'
                with open(os.path.join(settings.MEDIA_ROOT, 'app_images', image_name), 'wb') as f:
                    f.write(urllib.urlopen(app_icon_url).read())
                app.icon = os.path.join('app_images', image_name)

                app.description = self.wd.find_element_by_css_selector('div.id-app-orig-desc').text
                app.rating = Decimal(self.wd.find_element_by_css_selector('div.score-container meta').get_attribute('content'))
                app.downloads = self.wd.find_element_by_css_selector('div.content[itemprop=numDownloads]').text

                with db_lock:
                    app.save()

                app_images = [i.get_attribute('src') for i in self.wd.find_elements_by_css_selector('div.thumbnails img')]
                for app_image in app_images:
                    image_queue.put([app_image, app])


class Command(BaseCommand):
    def handle(self, keyword, *args, **options):
        Application.objects.all().delete()
        main_wd = webdriver.Firefox()
        # main_wd = webdriver.Chrome()
        main_wd.get('https://play.google.com/store/search?q=%s&c=apps' % quote(keyword))

        while True:
            more = True
            app_count = 0
            while more:
                apps = main_wd.find_elements_by_css_selector('div.card')
                apps[-5].location_once_scrolled_into_view
                time.sleep(2)
                if len(apps) == app_count:

                    break

                app_count = len(apps)
            try:
                main_wd.find_element_by_id('show-more-button').click()
            except ElementNotVisibleException:
                break

        app_id_list = [a.get_attribute('href').split('=')[-1].strip() for a in main_wd.find_elements_by_css_selector('a.title')]
        main_wd.close()

        for a in app_id_list:
            app_queue.put(a)

        app_queue.put(_stop)
        for _ in range(settings.SPYDER_THREADS):
            AppWorker().start()
            ImageWorker().start()

        while True:
            try:
                a = 1
            except KeyboardInterrupt:
                app_queue.put(_stop)
                image_queue.put(_stop)
