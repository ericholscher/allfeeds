#!/usr/bin/env python

from django.shortcuts import render_to_response
from django.template import RequestContext
from socialgraph.models import Request
from django.http import HttpResponse, Http404
from djangopeople.models import Service


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
