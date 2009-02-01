from django.conf.urls.defaults import *
from djangopeople.atom.feeds import PersonFeed, TagFeed, ServiceFeed, AllFeed
from djangopeople.models import BaseFeed, Member
from django.contrib import admin

admin.autodiscover()


feeds = {
    'person': PersonFeed,
    'service': ServiceFeed,
    'tag': TagFeed,
    'all': AllFeed,
}

urlpatterns = patterns('',

    url(r'profile/(?P<username>.*)/', 'djangopeople.views.profile', name='djangopeople_profile' ),

    url(r'members/', 'djangopeople.views.members', name='djangopeople_members' ),

    url(r'river/(?P<service>.*)/(?P<slug>.*)/', 'djangopeople.views.service_detail', name='djangopeople_service_river_detail'),
    url(r'river/(?P<service>.*)/', 'djangopeople.views.service', name='djangopeople_service_river'),
    url(r'river/(?P<service>.*)/username/(?P<username>.*)', 'djangopeople.views.service_username', name='djangopeople_service_username'),
    url(r'river/(?P<service>.*)/tag/(?P<tag>.*)', 'djangopeople.views.service_tag', name='djangopeople_service_tag'),
    url(r'^$', 'djangopeople.views.home', name='djangopeople_home'),

    (r'^tag/(?P<tag>.*)/', 'tagging.views.tagged_object_list', { 'queryset_or_model': BaseFeed.objects.all(), 'paginate_by': 50 } ),

    url(r'^feeds/(.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    )
