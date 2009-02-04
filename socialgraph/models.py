#!/usr/bin/env python

#!/usr/bin/env python

import simplejson as json
import urllib2
from django.db import models

query_url = "http://socialgraph.apis.google.com/lookup?q=%s&fme=1&edo=1&edi=1"

# node_cache = {}
class Request(models.Model):
    url = models.URLField(unique=True)
    canonical_mapping = models.URLField(blank=True)
    json_obj = models.TextField(blank=True)

    nodes_referenced = models.ManyToManyField('Request', related_name='nodes_referenced_by')
    claimed_nodes = models.ManyToManyField('Request', related_name='unverified_claiming_nodes')
    toplevel_nodes = models.ManyToManyField('Request', related_name='parents')
    #types?

    @property
    def python_obj(self):
        return json.JSONDecoder().decode(self.json_obj)

    def fetch_social_object(self, top_level=True):
        print "querying %s" % self.url
        resp = urllib2.urlopen(query_url % self.url)
        self.json_obj = resp.read()

    def populate_structure(self, fetch=False, recurse=False):
        if fetch:
            self.fetch_social_object()
            self.canonical_mapping = self.python_obj['canonical_mapping'].values()[0]

        if self.python_obj:
            for url,node in self.python_obj['nodes'].items():
                t, created = Request.get_or_create(url=url, python_obj=node)
                if recurse:
                    t.populate_structure(recurse=True)
                else:
                    t.populate_structure()
                self.toplevel_nodes.append(t)

            for claimed_node in self.python_obj.get('claimed_nodes', []):
                n = Node.get_or_create(claimed_node)
                if recurse:
                    n.populate_structure(recurse=True)
                self.claimed_nodes.append(n)

            for unverified_node in self.python_obj.get('unverified_claiming_nodes', []):
                n = Node.get_or_create(unverified_node)
                self.unverified_claiming_nodes.append(n)

            for name,types in self.python_obj.get('nodes_referenced',{}).iteritems():
                n = Node.get_or_create(name)
                if recurse:
                    n.populate_structure(recurse=True)
                n.types = types['types']
                self.nodes_referenced[name] = n

            for name,types in self.python_obj.get('nodes_referenced_by',{}).iteritems():
                n = Node.get_or_create(name)
                n.types = types['types']
                self.nodes_referenced_by[name] = n

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

if __name__ == '__main__':
    eric = Request('http://ericholscher.com')
    eric.populate_structure()
    daniel = Request('http://twitter.com/daniellindsley')
    daniel.populate_structure()
    matt = Request('djangopeople.net/mcroydon')
    matt.populate_structure()
    jacob = Request('jacobian.org')
    jacob.populate_structure()
