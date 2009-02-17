#!/usr/bin/env python

from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from socialgraph.views import socialgraph_json, get_friends, pretty_picture

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'example.html'} ),
    url(r'friends/', get_friends, name='sg_process_url' ),
    url(r'pretty/', pretty_picture, name='pretty' ),
    url(r'fetch/(?P<url>.*)', socialgraph_json, name='sg_json' ),
    )
