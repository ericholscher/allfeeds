#!/usr/bin/env python

import simplejson as json
import urllib2
from django.db import models

query_url = "http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edo=1&edi=1&pretty=1"

class Request(models.Model):
    url = models.URLField(unique=True, primary_key=True)
    canonical_mapping = models.URLField(blank=True, null=True, unique=True)
    json_obj = models.TextField(blank=True)

    nodes_referenced = models.ManyToManyField('Request', related_name='nodes_referenced_by', null=True)
    claimed_nodes = models.ManyToManyField('Request', related_name='unverified_claiming_nodes', null=True)
    toplevel_nodes = models.ManyToManyField('Request', related_name='parents', null=True)
    #types?

    def fetch_social_object(self, top_level=True):
        if self.json_obj:
            return self.json_obj
        print "querying %s" % self.url
        resp = urllib2.urlopen(query_url % self.url)
        self.json_obj = resp.read()
        self.save()
        return json.JSONDecoder().decode(self.json_obj)

    def populate_structure(self, fetch=False, recurse=False):
        if self.canonical_mapping:
            print "%s already exits" % self.url
            return
        try:
            python_obj = self.fetch_social_object()
        except:
            print "(HTTP) FAIL"
            return
        self.canonical_mapping = python_obj['canonical_mapping'].values()[0]

        if python_obj:
            for url,node in python_obj['nodes'].items():
                t, created = Request.objects.get_or_create(url=url)
                if recurse:
                    t.populate_structure(recurse=True)
                elif created:
                    t.populate_structure()
                self.toplevel_nodes.add(t)

                for claimed_node in node.get('claimed_nodes', []):
                    n, created = Request.objects.get_or_create(url=claimed_node)
                    if recurse:
                        n.populate_structure(recurse=True)
                    self.claimed_nodes.add(n)

                for name,types in node.get('nodes_referenced',{}).iteritems():
                    n, created = Request.objects.get_or_create(url=name)
                    if recurse:
                        n.populate_structure(recurse=True)
                    n.types = types['types']
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



    def loves(self, lover):
        my_nodes = self.urls_claimed
        lover_nodes = lover.urls_referenced
        for node in my_nodes:
            if node in lover_nodes:
                print "%s loves %s" % (lover, node)
                return True
        return False


    def __unicode__(self):
        return self.url

    def __str__(self):
        return self.url

    def __repr__(self):
        return "<Request object: %s>" % self.url


class Attributes(models.Model):
    request = models.ForeignKey(Request, related_name='attributes')

    def populate_structure(self):
        self.url = self.kwargs.get('url', '')
        self.profile = self.kwargs.get('profile', '')
        self.rss = self.kwargs.get('rss', '')
        self.atom = self.kwargs.get('atom', '')
        self.foaf = self.kwargs.get('foaf', '')
        self.photo = self.kwargs.get('photo', '')
        self.fn = self.kwargs.get('fn', '')
