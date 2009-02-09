#!/usr/bin/env python

import simplejson as json
import urllib2
from django.db import models
from django.template.defaultfilters import slugify
import graph
import gv


query_url = "http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edo=1&edi=1&pretty=1"

class Request(models.Model):
    url = models.URLField(unique=True)
    canonical_mapping = models.URLField(blank=True, null=True)
    slug = models.SlugField()
    json_obj = models.TextField(blank=True)

    claimed_nodes = models.ManyToManyField('Request', related_name='unverified_claiming_nodes', null=True, symmetrical=False)
    toplevel_nodes = models.ManyToManyField('Request', related_name='parents', null=True, symmetrical=False)
    #Need a through model here
    nodes_referenced = models.ManyToManyField('Request', through='Contact', related_name='nodes_referenced_by', null=True, symmetrical=False)
    #types?
    populated = models.BooleanField(default=False)

    @property
    def toplevel(self):
        return list(self.toplevel_nodes.all())

    @property
    def claimed(self):
        return list(self.claimed_nodes.all())

    @property
    def referenced(self):
        return list(self.nodes_referenced.all())




    def fetch_social_object(self):
        print "querying %s" % self.url
        resp = urllib2.urlopen(query_url % self.url)
        self.json_obj = resp.read()
        self.populated = True
        self.save()
        return json.JSONDecoder().decode(self.json_obj)

    def populate_structure(self, fill=False, force=False):
        if self.populated and not force:
            print "%s already populated" % self.url
            return
        try:
            python_obj = self.fetch_social_object()
        except Exception, e:
            print "(HTTP) FAIL: %s" % e
            return

        self.canonical_mapping = python_obj['canonical_mapping'].values()[0]
        self.populated = True

        if python_obj:
            for url,node in python_obj['nodes'].items():
                t, created = Request.objects.get_or_create(url=url)
                if fill:
                    t.populate_structure()
                self.toplevel_nodes.add(t)

                for claimed_node in node.get('claimed_nodes', []):
                    n, created = Request.objects.get_or_create(url=claimed_node)
                    self.claimed_nodes.add(n)

                for name,types in node.get('nodes_referenced',{}).iteritems():
                    n, created = Request.objects.get_or_create(url=name)
                    c, cr = Contact.objects.get_or_create(fro=node, to=n, types=types)
                    self.nodes_referenced.add(n)
                """
                for unverified_node in node.get('unverified_claiming_nodes', []):
                    n, created = Request.objects.get_or_create(url=unverified_node)
                    self.unverified_claiming_nodes.add(n)

                for name,types in node.get('nodes_referenced_by',{}).iteritems():
                    n, created = Request.objects.get_or_create(url=name)
                    n.types = types['types']
                    self.nodes_referenced_by[name] = n
                """
        self.save()

    def dot_file(self, referenced=False):
        gr = graph.digraph()
        gr.add_nodes([self.url])
        toplevel = self.toplevel_nodes.all()
        gr.add_nodes(list(toplevel))
        for node in toplevel:
            print "Making %s" % node
            gr.add_nodes([str(node)])
            gr.add_edge(self.url, str(node))
            for claimed in node.claimed_nodes.all():
                gr.add_nodes([str(claimed)])
                gr.add_edge(str(node), str(claimed))
        if referenced:
            for node in self.nodes_referenced.all():
                gr.add_nodes([str(node)])
                gr.add_edge(str(url), str(node))


        dot = gr.write(fmt='dot')
        """
        gvv = gv.readstring(dot)
        gv.layout(gvv,'dot')
        gv.render(gvv,'png','test.png')
        """
        return dot

    def __unicode__(self):
        return self.url

    def __str__(self):
        return self.url

    def __repr__(self):
        return "<Request object: %s>" % self.url

    def save(self, force_insert=False, force_update=False):
        temp_url = self.url
        temp_url = temp_url.replace('http://', '')
        #import ipdb; ipdb.set_trace()
        temp_url = temp_url.replace('www.', '')
        temp_url = temp_url.rstrip('/ ')
        self.slug = slugify(self.url)
        super(Request, self).save(force_insert, force_update)

CONTACT_TYPES = (
    ('me', 'me'),
    ('contact', 'contact'),
    ('acquaintance', 'acquaintance'),
    ('friend', 'friend'),
    ('met', 'met'),
    ('co-worker', 'co-worker'),
    ('colleague', 'colleague'),
    ('co-resident', 'co-resident'),
    ('neighbor', 'neighbor'),
    ('child', 'child'),
    ('parent', 'parent'),
    ('sibling', 'sibling'),
    ('spouse', 'spouse'),
    ('kin', 'kin'),
    ('muse', 'muse'),
    ('crush', 'crush'),
    ('date', 'date'),
    ('sweetheart', 'sweetheart'),
    )

class Contact(models.Model):
    to = models.ForeignKey(Request)
    fro = models.ForeignKey(Request)
    types = models.CharField(max_length=100)
