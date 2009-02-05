#!/usr/bin/env python

from django.shortcuts import render_to_response
from django.template import RequestContext
from socialgraph.models import Request
from django.http import HttpResponse, Http404


def socialgraph_json(request, url):
    r, created = Request.objects.get_or_create(url=url)
    if created:
        r.populate_structure()
    return HttpResponse(r.json_obj, mimetype='application/javascript')

def process_url(request):
    if request.POST:
        url = request.POST['url']
    else:
        return Http404('Please post, yo')

    r, created = Request.objects.get_or_create(url=url)
    if created:
        r.populate_structure()
    return HttpResponse(r.json_obj, mimetype='application/javascript')
