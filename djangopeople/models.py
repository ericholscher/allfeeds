from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from tagging.fields import TagField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from djangopeople.managers import SubdomainManager


class Service(models.Model):
    """
    Flickr, Delicious, Blog
    """
    name = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    url = models.CharField(max_length=200, blank=True )
    user_template = models.CharField(max_length=200, blank=True)
    userfeed_template = models.CharField(max_length=200, blank=True)
    tagfeed_template = models.CharField(max_length=200, blank=True)
    public_feed = models.CharField(max_length=200, blank=True)
    active = models.BooleanField()
    uses_api = models.BooleanField()

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False):
        self.slug = slugify(self.name)
        super(Service, self).save(force_insert, force_update)

class Member(models.Model):
    """
    Class representing a member that has a feed being pulled in
    May or may not represent a User

    Service Entries allow us to point to any arbitrary Service Entry
    """
    user = models.ForeignKey(User, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    site_url = models.CharField(max_length=200)

    tags = TagField()

    def __unicode__(self):
        return self.name

    def feed_for_service(self, service):
        entry = self.service_entries.get(service_slug=service)
        if service == 'personal-blog':
            return entry.feed_url
        return entry.service.userfeed_template % entry.username

    def username_for_service(self, service):
        return self.service_entries.get(service_slug=service).username

    def save(self, force_insert=False, force_update=False):
        self.slug = slugify(self.name)
        super(Member, self).save(force_insert, force_update)

class ServiceEntry(models.Model):
    """My flickr, my blog, my delicious

    This will point to any arbitrary service
    """
    service = models.ForeignKey(Service, related_name="service_entries")
    #Should have a member 99% of the time, if it doesn't have a tag
    member = models.ForeignKey(Member, null=True, blank=True, related_name="service_entries")
    profile_url = models.CharField(max_length=200, unique=True)
    feed_url = models.CharField(max_length=200, blank=True)

    desc = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=5, blank=True)
    username = models.CharField(max_length=200, blank=True)
    tag = models.CharField(max_length=200, blank=True)
    #trusted = models.BooleanField(default=False)

    # http://feedparser.org/docs/http-etag.html
    etag = models.CharField(max_length=50, blank=True)
    last_modified = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    tags = TagField()

    def __unicode__(self):
        return "%s" % (self.profile_url)

class Subdomain(models.Model):
    #Allow users a toplevel subdomain ex. eric.allfeeds.net
    user = models.ForeignKey(User, null=True, blank=True, related_name="subdomain")
    #For django.allfeeds.net, no user, but follow people
    members = models.ManyToManyField(Member, null=True, blank=True, related_name="subdomains")

    #slug.allfeeds.net
    slug = models.SlugField(unique=True, blank=True)
    #This is where we pull our data from.
    source_url = models.CharField(max_length=200, blank=True)
    #This will probably be checked daily, for new users from the agg
    last_user_check = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.slug

class BaseFeed(models.Model):
    """Display entry in toplevel stream, but not detail page, useful for sorting

    This will point to any generic Feed Type
    """
    service_entry = models.ForeignKey(ServiceEntry, null=True, blank=True, related_name='entries')
    service = models.ForeignKey(Service, null=True, blank=True, related_name='entries')
    member = models.ForeignKey(Member, related_name='entries', blank=True, null=True)
    subdomain = models.ForeignKey(Subdomain, related_name='entries', blank=True, null=True)

    slug = models.SlugField(blank=True)
    published = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    link = models.URLField(max_length=255, verify_exists=False, null=True, blank=True )
    guid = models.CharField(max_length=255, unique=True)

    tags = TagField()

    #Generic relation to Actual BaseFeed
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = SubdomainManager()


    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('djangopeople_service_river_detail', args=[self.service.slug, self.slug])

    def get_river_url(self):
        return reverse('djangopeople_service_river', args=[self.service.slug])

    def get_profile_river_url(self):
        return reverse('djangopeople_profile', args=[self.member_slug])

    def get_icon_url(self):
        return "http://media.ericholscher.com/images/services/%s.png" % self.service.slug

    class Meta:
        ordering = ['-published']
        verbose_name = 'Base Feed'
        verbose_name_plural = 'Base Feeds'

    def save(self, force_insert=False, force_update=False):
        self.slug = slugify(self.guid)
        super(BaseFeed, self).save(force_insert, force_update)

"""
class TwitterFeed(BaseFeed):
    twitter_username = models.CharField(max_length=30)
"""
