#!/usr/bin/env python

from django.template.defaultfilters import capfirst

def populate_subdomain(request):
    return {'SUB': request.subdomain,
            'site_name': capfirst(request.subdomain),
            'subdomain': request.subdomain}
