#!/usr/bin/env python

from django.conf.urls.defaults import *
from django.contrib import admin
from socialgraph.views import socialgraph_json, process_url

admin.autodiscover()


urlpatterns = patterns('',
    url(r'json_url/', process_url, name='sg_process_url' ),
    url(r'(?P<url>.*)/', socialgraph_json, name='sg_json' ),
    )
