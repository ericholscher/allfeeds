#!/usr/bin/env python

from django.shortcuts import render_to_response
from django.template import RequestContext
from socialgraph.models import Request
from django.http import HttpResponse, Http404, HttpResponseRedirect
from djangopeople.models import Service
import pygraphviz
import shutil
import os
import re


def socialgraph_json(request, url):
    r, created = Request.objects.get_or_create(url=url)
    if created or not r.populated:
        r.populate_structure()
    return HttpResponse(r.json_obj, mimetype='application/javascript')

def get_friends(request):
    if request.POST:
        twitter = "http://twitter.com/" +  request.POST['twitter']
    else:
        return Http404('Please post, yo')

    twitter2 = ""
    if request.POST.has_key('twitter2'):
        twitter2 = "http://twitter.com/" +  request.POST['twitter2']

    r, created = Request.objects.get_or_create(url=twitter)
    if created or not r.populated:
        r.populate_structure(force=True)

    r2, created = Request.objects.get_or_create(url=twitter2)
    if created or not r.populated:
        r.populate_structure(force=True)
    claimed = list(r.claimed_nodes.all())
    friends = r.nodes_referenced.all()
    fake_friends = r.nodes_referenced_by.all()
    #ret_val = ["%s\n" % c.url for c in claimed]
    services = Service.objects.exclude(user_template='')
    ret_val = '{\n'
    for service in services:
        service_feed = service.user_template.replace('%s','(\w+)')
        srv_re = re.compile(service_feed)
        for url in [u.url for u in claimed]:
            match = srv_re.search(url)
            if match:
                ret_val += "'%s': '%s',\n" % (service.slug, match.group(1))

    ret_val += "}\n\n"

    friends = r.nodes_referenced.all()
    friends2 = r2.nodes_referenced.all()
    for friend in friends2:
        if friend in friends:
            ret_val += "LOVE <-> %s\n" % friend


    fake_friends = r.nodes_referenced_by.all()
    for friend in friends:
        if friend in fake_friends:
            ret_val += "LOVE %s\n" % friend
    #ret_val += "\n".join(["friend ->: %s \n" % f.url for f in list(friends)])
    #ret_val += "\n".join(["<- friend: %s \n" % f.url for f in list(fake_friends)])
    #ret_val += ("\n\n\n%s" % r.json_obj)
    return HttpResponse("<pre>%s</pre>" % ret_val, mimetype='application/javascript')


def pretty_picture(request):
    if request.POST:
        twitter = "http://twitter.com/" +  request.POST['twitter']
    else:
        return Http404('Please post, yo')

    layout = "dot"
    if request.POST.has_key('layout'):
        layout = request.POST['layout']

    filename = type = "claimed"
    if request.POST.has_key('type'):
        filename = type = request.POST['type']

    format = "png"
    if request.POST.has_key('format'):
        format = request.POST['format']

    rnode, created = Request.objects.get_or_create(url=twitter)
    if created or not rnode.populated:
        rnode.populate_structure(fill=True)


    fname = '%s_%s.%s' % (filename, layout, format)
    dirname = rnode.slug
    dest_dir = '/var/www/af/media/%s' % dirname
    dest_file = os.path.join(dest_dir, fname)
    redir_file = '/media/%s/%s' % (dirname, fname)

    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    #This will comment out when debugging
    if os.path.exists(dest_file):
        return render_to_response('pretty.html', {'file_path': redir_file})

    if type == "claimed":
        dot = rnode.dot_file(referenced=False)
    else:
        dot = rnode.dot_file(referenced=True)
    pygv = pygraphviz.AGraph(dot)
    pygv.graph_attr['label']='Social Graph'
    pygv.node_attr['shape']='square'
    pygv.layout(prog=layout)
    pygv.draw(dest_file)
    return HttpResponse('<img alt="Pretty picture" src="%s">' % redir_file)
