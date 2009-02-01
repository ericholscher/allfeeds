from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site

import mptt
from pages import settings
from pages.managers import PageManager, ContentManager, PagePermissionManager

try:
    tagging = models.get_app('tagging')
    from tagging.fields import TagField
except ImproperlyConfigured:
    tagging = False

if not settings.PAGE_TAGGING:
    tagging = False

class Page(models.Model):
    """
    A simple hierarchical page model
    """
    # some class constants to refer to, e.g. Page.DRAFT
    DRAFT = 0
    PUBLISHED = 1
    EXPIRED = 2
    STATUSES = (
        (DRAFT, _('Draft')),
        (PUBLISHED, _('Published')),
    )
    author = models.ForeignKey(User)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    publication_date = models.DateTimeField(null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'))
    publication_end_date = models.DateTimeField(null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'))

    status = models.IntegerField(choices=STATUSES, default=DRAFT)
    template = models.CharField(max_length=100, null=True, blank=True)
    sites = models.ManyToManyField(Site, default=[settings.SITE_ID], help_text=_('The site(s) the page is accessible at.'))

    # Managers
    objects = PageManager()

    if tagging:
        tags = TagField()

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    def save(self, *args, **kwargs):
        if not self.status:
            self.status = self.DRAFT
        # Published pages should always have a publication date
        if self.publication_date is None and self.status == self.PUBLISHED:
            self.publication_date = datetime.now()
        # Drafts should not, unless they have been set to the future
        if self.status == self.DRAFT:
            if settings.PAGE_SHOW_START_DATE:
                if self.publication_date and self.publication_date <= datetime.now():
                    self.publication_date = None
            else:
                self.publication_date = None
        super(Page, self).save(*args, **kwargs)

    def get_calculated_status(self):
        """
        get the calculated status of the page based on published_date,
        published_end_date, and status
        """
        if settings.PAGE_SHOW_START_DATE:
            if self.publication_date > datetime.now():
                return self.DRAFT
        
        if settings.PAGE_SHOW_END_DATE and self.publication_end_date:
            if self.publication_end_date < datetime.now():
                return self.EXPIRED

        return self.status
    calculated_status = property(get_calculated_status)
        
    def get_languages(self):
        """
        get the list of all existing languages for this page
        """
        contents = Content.objects.filter(page=self, type="title")
        languages = []
        for c in contents:
            if c.language not in languages:
                languages.append(c.language)
        return languages

    def get_absolute_url(self, language=None):
        return reverse('pages-root') + self.get_url(language)

    def get_url(self, language=None):
        """
        get the url of this page, adding parent's slug
        """
        if settings.PAGE_UNIQUE_SLUG_REQUIRED:
            url = u'%s/' % self.slug(language)
        else:
            url = u'%s-%d/' % (self.slug(language), self.id)
        for ancestor in self.get_ancestors(ascending=True):
            url = ancestor.slug(language) + u'/' + url
        return url

    def slug(self, language=None, fallback=True):
        """
        get the slug of the page depending on the given language
        """
        if not language:
            language = settings.PAGE_DEFAULT_LANGUAGE
        return Content.objects.get_content(self, language, 'slug',
                                           language_fallback=fallback)

    def title(self, language=None, fallback=True):
        """
        get the title of the page depending on the given language
        """
        if not language:
            language = settings.PAGE_DEFAULT_LANGUAGE
        return Content.objects.get_content(self, language, 'title',
                                           language_fallback=fallback)

    def get_template(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        if self.template:
            return self.template
        for p in self.get_ancestors(ascending=True):
            if p.template:
                return p.template
        return settings.DEFAULT_PAGE_TEMPLATE

    def traductions(self):
        langs = ""
        for lang in self.get_languages():
            langs += '%s, ' % lang
        return langs[0:-2]

    def has_page_permission(self, request):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if not settings.PAGE_PERMISSION:
            return True
        else:
            permission = PagePermission.objects.get_page_id_list(request.user)
            if permission == "All":
                return True
            if self.id in permission:
                return True
            return False

    def __unicode__(self):
        slug = self.slug()
        # when created in console mode, page has no slug
        if slug is None:
            return "Page %d" % self.id
        return slug

# Don't register the Page model twice.
try:
    mptt.register(Page)
except mptt.AlreadyRegistered:
    pass

if settings.PAGE_PERMISSION:
    class PagePermission(models.Model):
        """
        Page permission object
        """
        TYPES = (
            (0, _('All')),
            (1, _('This page only')),
            (2, _('This page and all childrens')),
        )
        page = models.ForeignKey(Page, null=True, blank=True)
        user = models.ForeignKey(User)
        type = models.IntegerField(choices=TYPES, default=0)
        
        objects = PagePermissionManager()
        
        def __unicode__(self):
            return "%s :: %s" % (self.user, unicode(PagePermission.TYPES[self.type][1]))

class Content(models.Model):
    """A block of content, tied to a page, for a particular language"""
    language = models.CharField(max_length=3, blank=False)
    body = models.TextField()
    type = models.CharField(max_length=100, blank=False)
    page = models.ForeignKey(Page)

    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    objects = ContentManager()

    def __unicode__(self):
        return "%s :: %s" % (self.page.slug(), self.body[0:15])
