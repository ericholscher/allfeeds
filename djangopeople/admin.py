from djangopeople.models import Member, BaseFeed, Service, ServiceEntry, Subdomain
from django.contrib import admin

class ServiceEntryInline(admin.TabularInline):
    model = ServiceEntry
    fields = ('service', 'profile_url', 'feed_url', 'username')

class SubdomainInline(admin.TabularInline):
    model = Subdomain


class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    inlines = [
        ServiceEntryInline,
    ]

class ServiceAdmin(admin.ModelAdmin):
	list_display = ['name', 'active', 'userfeed_template']

class ServiceEntryAdmin(admin.ModelAdmin):
    list_display = ['member', 'service']
    list_filter = ['service']
    search_fields = ['username', 'feed_url']


class SubdomainAdmin(admin.ModelAdmin):
	list_display = ['slug', 'source_url']

class BaseFeedAdmin(admin.ModelAdmin):
	search_fields = ['title']
	list_display = ['title', 'member', 'slug', 'published']
	list_filter = ['service']
	date_hierarchy = 'published'

admin.site.register(BaseFeed, BaseFeedAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceEntry, ServiceEntryAdmin)
admin.site.register(Subdomain, SubdomainAdmin)
