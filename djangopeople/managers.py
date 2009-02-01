from django.db.models import Manager
import datetime

class SubdomainManager(Manager):
    """Returns published posts that are not in the future."""

    def subdomain(self, subdomain):
        return self.get_query_set().filter(service_entry__member__subdomains=subdomain)
