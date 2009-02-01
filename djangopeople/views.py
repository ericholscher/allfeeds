# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from BeautifulSoup import BeautifulSoup
from django.core.exceptions import *
import datetime
from djangopeople.models import Member, BaseFeed, Subdomain, Service
from djangopeople.utils import _get_subdomain
from django.db.models import Q
from django.http import HttpResponsePermanentRedirect

def home(request):
    sub = _get_subdomain(request)
    entries = BaseFeed.objects.filter(service_entry__subdomains=sub)[:50]
    services = Service.objects.filter(active=True)
    return render_to_response('djangopeople/home.html', {'entries': entries,
                                                         'services': services},
                    context_instance=RequestContext(request))

def members(request):
    sub = _get_subdomain(request)
    members = sub.members.all()
    return render_to_response('djangopeople/members.html', {'members': members },
                    context_instance=RequestContext(request))

def service(request, service):
    sub = _get_subdomain(request)
    base_sub = BaseFeed.objects.subdomain(sub)
    if service == 'all':
        objects = base_sub.all()[:20]
    else:
        service = Service.objects.get(slug=service)
        objects = base_sub.filter(service=service)[:100]
    return render_to_response('djangopeople/river.html', {'riverof': service, 'objects': objects },
        context_instance=RequestContext(request))

def service_tag(request, service, tag):
    pass

def service_detail(request, service, slug):
    serv = Service.objects.get(slug=service)
    en = BaseFeed.objects.get(service=serv, slug=slug)
    return render_to_response('djangopeople/entry_detail.html', {'object': en },
            context_instance=RequestContext(request))

def service_username(request, service, username):
    mem = Member.objects.get(slug=username)
    serv = Service.objects.get(slug=service)
    objects = BaseFeed.objects.filter(service_entry__member=mem, service_entry__service=serv)[:100]
    return render_to_response('djangopeople/river.html', {'riverof': service, 'objects': objects },
            context_instance=RequestContext(request))

def profile(request, username):
    mem = Member.objects.get(slug=username)
    entries = BaseFeed.objects.filter(service_entry__member=mem)[:20]
    services = mem.service_entries.all()
    return render_to_response('djangopeople/profile.html', {'member': mem,
                                                            'entries': entries,
                                                            'services': services},
				  context_instance=RequestContext(request))
