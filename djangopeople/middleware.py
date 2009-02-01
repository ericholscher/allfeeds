#!/usr/bin/env python

class GetSubdomainMiddleware:
    """ Make the subdomain publicly available to classes """

    def process_request(self, request):
        domain_parts = request.META['HTTP_HOST'].split('.')
        if (len(domain_parts) > 2):
            subdomain = domain_parts[0]
            if (subdomain.lower() == 'www'):
                subdomain = 'django'
            domain = '.'.join(domain_parts[1:])
        else:
            subdomain = 'django'
            domain = request.META['HTTP_HOST']

        request.subdomain = subdomain
