#!/usr/bin/env python

from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from socialgraph.views import socialgraph_json, process_url, pretty_picture, friend_picture

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'example.html'} ),
    url(r'json_url/', process_url, name='sg_process_url' ),
    url(r'pretty/(?P<url>.*)', pretty_picture, name='pretty' ),
    url(r'friends/(?P<url>.*)', friend_picture, name='friends' ),
    url(r'fetch/(?P<url>.*)', socialgraph_json, name='sg_json' ),
    )
