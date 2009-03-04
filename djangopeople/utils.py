#!/usr/bin/env python

from djangopeople.models import Subdomain
import logging
import time
from djangopeople.models import Member, BaseFeed, Service
#from djangopeople.providers.agg import create_user
import feedparser
import datetime
from dateutil import parser
from tagging.models import Tag
from django.conf import settings

from django.db import transaction

log = logging.getLogger("djangopeople.utils")

def _get_subdomain(request):
    """
    Pulled this out into a util function because this logic may change.
    Also not sure if subdomain is the right logic, but it'll work for now.
    """
    return Subdomain.objects.get(slug=request.subdomain)

@transaction.commit_on_success
def update_feed(service_entry, subdomain=None):
    "Feed entry dispatcher"
    try:
        log.info("Updating %s on %s" % (service_entry, subdomain))
    except:
        pass
    if service_entry.service.uses_api and not service_entry.tag:
        _update_using_api(service_entry, subdomain)
    else:
        _update_using_rss(service_entry, subdomain)

def _get_feed_data(feed, feeds):
    try:
        #Gracously stolen from Django Community Agg code.
        title = feed.title.encode(feeds.encoding, "xmlcharrefreplace")
        guid = feed.get("id", feed.link).encode(feeds.encoding, "xmlcharrefreplace")
        link = feed.link.encode(feeds.encoding, "xmlcharrefreplace")

        if not guid:
            guid = link

        if hasattr(feed, "summary"):
            content = feed.summary
        elif hasattr(feed, "content"):
            content = feed.content[0].value
        elif hasattr(feed, "description"):
            content = feed.description
        else:
            content = u""
        content = content.encode(feeds.encoding, "xmlcharrefreplace")

        try:
            if feed.has_key('modified_parsed'):
                date_modified = datetime.datetime.fromtimestamp(time.mktime(feed.modified_parsed))
            elif feeds.feed.has_key('modified_parsed'):
                date_modified = datetime.datetime.fromtimestamp(time.mktime(feeds.feed.modified_parsed))
            elif feeds.has_key('modified'):
                date_modified = datetime.datetime.fromtimestamp(time.mktime(feeds.modified))
            else:
                date_modified = datetime.datetime.now()
        except TypeError:
            date_modified = datetime.datetime.now()

        tags = []
        if feed.has_key('tags'):
            tags = [tag['term'] for tag in feed.tags]

        #if :
        return (title, date_modified, link, content, guid, tags)
#        else:
            #return (title, date_modified, link, content, guid, tags, kwargs)
        #return locals()
    except Exception, e:
        print "Feed parse fail: %s" % e
        pass

def _update_using_rss(service_entry, subdomain):
    if service_entry.feed_url:
        print "updating %s" % service_entry.feed_url
        etag = service_entry.etag
        feeds = feedparser.parse(service_entry.feed_url, etag=etag, agent="Allfeeds.net 0.1, Python Community Aggregator")

        if hasattr(feeds, 'status'):
            print "Status: %s" % feeds.status
            if feeds.status == 304:
                log.info('[%s] Feed has not changed since last check' %
                         service_entry.feed_url)
                return feeds.status

            if feeds.status >= 400:
                # http error, ignore
                log.info('!HTTP_ERROR! %d: %s' % (feeds.status,
                                                     service_entry.feed_url))
                return feeds.status


        #Feed is updated.
        service_entry.etag = feeds.get('etag', '')
        if service_entry.etag is None:
            service_entry.etag = ''

        service_entry.last_checked = datetime.datetime.now()
        service_entry.save()

        for feed in feeds.entries:
            try:
                create_entry_from_data(service_entry, subdomain, *_get_feed_data(feed, feeds))
            except:
                pass

def _update_using_api(service_entry, subdomain):
    user_for_service = service_entry.username
    print "updating %s for %s" % (user_for_service, service_entry.service)
    try:
        if service_entry.service.slug == 'friendfeed':
            from friendfeed import FriendFeed
            ff = FriendFeed()
            ffeed = ff.fetch_user_feed(user_for_service)
            for feed in ffeed.get('entries'):
                create_entry_from_data(service_entry=service_entry,
                                       subdomain=subdomain,
                                        title=feed.get('title'),
                                        date_modified=feed.get('published'),
                                        link=feed.get('link'),
                                        content=feed.get('title'),
                                        guid=feed.get('id'))
        elif service_entry.service.slug == 'twitter':
            import twitter
            api = twitter.Api(username=getattr(settings, 'TWITTER_USERNAME', ''), password=getattr(settings, 'TWITTER_PASSWORD', ''))
            statuses = api.GetUserTimeline(user_for_service)
            for status in statuses:
                pydate = parser.parse(status.created_at).replace(tzinfo=None)
                pylink = 'http://twitter.com/%s/status/%s/' % (user_for_service, status.id)
                create_entry_from_data(service_entry=service_entry,
                                       subdomain=subdomain,
                                        title=status.text,
                                        date_modified=pydate,
                                        link=pylink,
                                        content=status.text,
                                        guid=pylink)
    except Exception, e:
        log.error("%s fail: %s" % (service_entry, e))

def create_entry_from_data(service_entry, subdomain, title, date_modified, link, content, guid, tags='', **kwargs):
    #TODO: Figure out what model to use based on service
    if not subdomain:
        try:
            subdomain = service_entry.member.subdomains.all()[0]
        except:
            pass
    try:
        BaseFeed.objects.get(guid=guid)
        print "Already exists: %s" % guid
        return
    except BaseFeed.DoesNotExist:
        print "creating new object"
        try:
            entry, created = BaseFeed.objects.get_or_create(member=service_entry.member,
                                                        service_entry=service_entry,
                                                        service=service_entry.service,
                                                        subdomain = subdomain,
                                                        title=title,
                                                        published=date_modified,
                                                        link=link,
                                                        content=content,
                                                        guid=guid)
            if created:
                log.info("Created %s: %s" % (service_entry, title))
                if tags:
                    Tag.objects.update_tags(entry, ' '.join(set([tag.lower() for tag in tags])))
        except Exception, e:
            print "DB ERROR ON DATA CREATION: %s" % e
            pass
