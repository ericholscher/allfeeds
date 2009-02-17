
from django.core.management.base import BaseCommand, CommandError
import optparse
from djangopeople.utils import update_feed
from djangopeople.providers.agg import _update_user_list, _update_socialgraph
from djangopeople.models import Member, Subdomain, Service, ServiceEntry
import logging
from urlparse import urlparse
from django.conf import settings

"""
This file is best used in the following order
./manage.py syncdb
./manage.py updatefeeds -d django -G
./manage.py updatefeeds -d django -B
./manage.py updatefeeds -d django -L
./manage.py updatefeeds -d django -F
./manage.py updatefeeds
"""

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-s", "--service",
            dest="service",
            action="store",
            help="Pass in a service slug to update that service."
        ),
        optparse.make_option(
            "-m", "--member",
            action="store",
            dest="member",
            help="pass in a member slug to update just that member."
        ),
        optparse.make_option(
            "-d", "--subdomain",
            action="store",
            dest="subdomain",
            help="pass in a subdomain slug to update just that member."
        ),
        optparse.make_option(
            "-G", "--update-socialgraph",
            dest="update_socialgraph",
            action="store_true",
            help="Update the social graph for a subdomain."
        ),
        optparse.make_option(
            "-F", "--update-feeds",
            dest="update_feeds",
            action="store_true",
            help="Update the feeds from a subdomain."
        ),
        optparse.make_option(
            "-B", "--update-base",
            dest="update_base",
            action="store_true",
            help="Update the social graph based on users base url."
        ),
        optparse.make_option(
            "-L", "--loose",
            dest="loose",
            action="store_true",
            help="Update the social graph based on loose connections."
        ),    )

    def handle(self, *args, **options):

        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: %(message)s',
<<<<<<< HEAD:djangopeople/management/commands/updatefeeds.py
                    filename=settings.CRON_LOG_PATH,
                    filemode='a'
=======
                    #filename='/home/eric/.cron.log',
                    #filemode='a'
>>>>>>> github/dev:djangopeople/management/commands/updatefeeds.py
                   )

        update_feeds = options.get('update_feeds', False)
        update_socialgraph = options.get('update_socialgraph', False)
        update_base = options.get('update_base', False)
        loose = options.get('loose', False)
        member = options.get('member', '')
        service = options.get('service', '')
        subdomain = options.get('subdomain', '')

        if member:
            member = Member.objects.get(slug=member)
        if service:
            service = Service.objects.get(slug=service)
        if subdomain:
            subdomain = Subdomain.objects.get(slug=subdomain)

        #Actions performed on members
        if member and update_socialgraph:
            print "Updating a members profile information from the social graph"
            _update_socialgraph(member)

        elif member and update_feeds:
            print "Updated all of a users feeds"
            for service_entry in member.service_entries.all():
                update_feed(service_entry=service_entry)

        elif member and update_feeds and service:
            print "Updating a service for a member"
            service_entry = member.service_entries.get(service=service)
            update_feed(service_entry=service_entry)

        #Actions performed on subdomains
        elif subdomain and update_socialgraph:
            print "Updating social graph for all users in subdomain %s" % subdomain
            _update_user_list(subdomain)
            for mem in subdomain.members.all():
                print "Updating %s's social graph" % mem
                _update_socialgraph(mem)

        elif subdomain and update_feeds and service:
            print "Updating feeds for a service in subdomain"
            for service_entry in subdomain.service_entries.all():
                update_feed(service_entry=service_entry, subdomain=subdomain)

        elif subdomain and update_feeds:
            print "Updating _all_ feeds for all users in subdomain"
            for service_entry in ServiceEntry.objects.filter(member__subdomains=subdomain):
                update_feed(service_entry=service_entry, subdomain=subdomain)

            for service_entry in subdomain.service_entries.all():
                update_feed(service_entry=service_entry, subdomain=subdomain)

        #Actions performed on services
        elif update_feeds and service:
            print "Updating all feeds for a service"
            for service_entry in service.service_entries.filter(service__active=True):
                update_feed(service_entry=service_entry)

        elif update_base and subdomain:
            print "Updating subdomain from base urls"
            for mem in subdomain.members.all():
                parsed = urlparse(mem.site_url)
                url = "http://%s" % parsed.hostname
                _update_socialgraph(mem, url=url)

        elif subdomain and loose:
            print "Slutting out all the members"
            for mem in subdomain.members.all():
                parsed = urlparse(mem.site_url)
                url = "http://%s" % parsed.hostname
                _update_socialgraph(mem, url=url, loose=loose)

        #Everything
        elif update_feeds:
            print "Updating ALL feeds"
            for service_entry in ServiceEntry.objects.filter(service__active=True):
                update_feed(service_entry=service_entry)
