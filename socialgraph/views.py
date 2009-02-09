#!/usr/bin/env python

from django.shortcuts import render_to_response
from django.template import RequestContext
from socialgraph.models import Request
from django.http import HttpResponse, Http404, HttpResponseRedirect
from djangopeople.models import Service
import graph
import gv
import shutil
import os


def socialgraph_json(request, url):
    r, created = Request.objects.get_or_create(url=url)
    if created or not r.populated:
        r.populate_structure()
    return HttpResponse(r.json_obj, mimetype='application/javascript')

def process_url(request):
    if request.POST:
        url = request.POST['url']
    else:
        return Http404('Please post, yo')

    r, created = Request.objects.get_or_create(url=url)
    if created or not r.populated:
        r.populate_structure()
    #ret_val = r.json_obj
    claimed = list(r.claimed_nodes.all())
    fake_friends = Request.objects.filter(nodes_referenced__in=r.claimed_nodes.all()).distinct()
    friends = fake_friends.in_bulk([r.id for r in r.nodes_referenced.all()]).values()
    #friends = r.nodes_referenced.all().distinct()
    ret_val = "%s = %s" % (len(fake_friends), len(friends))
    #ret_val = ["friend ->: %s \n" % url for url in friends]
    #ret_val += ["<- friend: %s \n" % url for url in fake_friends]
    #ret_val.append("\n\n\n%s" % r.json_obj)
    return HttpResponse(ret_val, mimetype='application/javascript')


def pretty_picture(request, url):
    rnode, created = Request.objects.get_or_create(url=url)
    if created or not rnode.populated:
        rnode.populate_structure(fill=True)
    dirname = rnode.slug
    dest_dir = '/var/www/af/media/%s' % dirname
    dest_file = os.path.join(dest_dir, 'claimed.png')
    redir_file = '/media/%s/claimed.png' % dirname

    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    if os.path.exists(dest_file):
        return render_to_response('pretty.html', {'file_path': redir_file})

    dot = rnode.dot_file()
    gvv = gv.readstring(dot)
    gv.layout(gvv,'dot')

    #Hack so it'll make the right file
    old_cwd = os.getcwd()
    os.chdir(dest_dir)
    gv.render(gvv, 'png', 'claimed.png')
    os.chdir(old_cwd)
    return render_to_response('pretty.html', {'file_path': redir_file})

def friend_picture(request, url):
    pass
