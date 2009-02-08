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

    nodes_referenced = models.ManyToManyField('self', related_name='nodes_referenced_by', null=True)
    claimed_nodes = models.ManyToManyField('self', related_name='unverified_claiming_nodes', null=True)
    toplevel_nodes = models.ManyToManyField('self', related_name='parents', null=True)
    #types?
    populated = models.BooleanField(default=False)

    def fetch_social_object(self):
        #if self.populated:
            #return self.json_obj
        print "querying %s" % self.url
        resp = urllib2.urlopen(query_url % self.url)
        self.json_obj = resp.read()
        self.save()
        return json.JSONDecoder().decode(self.json_obj)

    def populate_structure(self):
        if self.populated:
            print "%s already populated" % self.url
            return
        try:
            python_obj = self.fetch_social_object()
        except:
            print "(HTTP) FAIL"
            return

        self.canonical_mapping = python_obj['canonical_mapping'].values()[0]
        self.populated = True

        if python_obj:
            for url,node in python_obj['nodes'].items():
                t, created = Request.objects.get_or_create(url=url)
                t.populate_structure()
                self.toplevel_nodes.add(t)

                for claimed_node in node.get('claimed_nodes', []):
                    n, created = Request.objects.get_or_create(url=claimed_node)
                    self.claimed_nodes.add(n)

                for name,types in node.get('nodes_referenced',{}).iteritems():
                    n, created = Request.objects.get_or_create(url=name)
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

    def pretty_picture(self):
        if not self.populated:
            self.populate_structure()

        gr = graph.graph()
        gr.add_nodes([self.url])
        toplevel = self.toplevel_nodes.all()
        gr.add_nodes(list(toplevel))
        for node in toplevel:
            print "Making %s" % node
            gr.add_nodes([str(node)])
            gr.add_edge(self.url, str(node))

        dot = gr.write(fmt='dot')
        gvv = gv.readstring(dot)
        gv.layout(gvv,'dot')
        gv.render(gvv,'png','test.png')

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
