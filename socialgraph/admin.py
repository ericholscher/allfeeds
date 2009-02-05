#!/usr/bin/env python
from django.contrib import admin
from socialgraph.models import Request

class RequestAdmin(admin.ModelAdmin):
    search_fields = ['url']

admin.site.register(Request, RequestAdmin)
