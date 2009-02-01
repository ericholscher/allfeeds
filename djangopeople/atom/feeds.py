from djangopeople.models import BaseFeed, Member
import atompub
from tagging.models import Tag, TaggedItem

class PersonFeed(atompub.Feed):

    def feed_id(self):
        return '1337'

    def feed_authors(self, obj):
        return [{'name': obj.name }]

    def get_object(self,bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Member.objects.get(slug=bits[0])

    def feed_title(self, obj):
        return "River for %s" % obj

    def items(self, obj):
        return obj.entries.all()[:20]

    def item_id(self, obj):
        return str(obj.id)

    def item_title(self, obj):
        return  '%s: %s' % (obj.member.name, obj.title)

    def item_links(self, obj):
        return [{'href': obj.link }]

    def item_updated(self, obj):
        return obj.published

    def item_categories(self, obj):
        tags = Tag.objects.get_for_object(obj)
        ret = []
        for tag in tags:
            ret.append({'term': tag.name })
        return ret

    def item_content(self, obj):
        ret = getattr(obj, 'content')
        if not ret:
            ret = obj.title
        return {'type': 'html'}, ret


class ServiceFeed(atompub.Feed):

    def get_object(self,params):
        return params[0]

    def feed_id(self):
        return '1339'

    def feed_authors(self, obj):
        return [{'name': obj }]

    def feed_title(self, obj):
        return "River for %s" % obj

    def items(self, obj):
        return BaseFeed.objects.filter(service__slug=obj)[:20]

    def item_id(self, obj):
        return str(obj.id)

    def item_title(self, obj):
        return  '%s: %s' % (obj.member.name, obj.title)

    def item_links(self, obj):
        return [{'href': obj.link }]

    def item_updated(self, obj):
        return obj.published

    def item_categories(self, obj):
        tags = Tag.objects.get_for_object(obj)
        ret = []
        for tag in tags:
            ret.append({'term': tag.name })
        return ret

    def item_content(self, obj):
        ret = getattr(obj, 'content')
        if not ret:
            ret = obj.title
        return {'type': 'html'}, ret



class TagFeed(atompub.Feed):

    def get_object(self,params):
        return Tag.objects.get(name=params[0])

    def feed_id(self):
        return '1336'

    def feed_authors(self, obj):
        return [{'name': obj.name }]

    def feed_title(self, obj):
        return "River for %s" % obj.name

    def items(self, obj):
        return TaggedItem.objects.get_by_model(BaseFeed.objects.all(), obj)

    def item_id(self, obj):
        return str(obj.id)

    def item_title(self, obj):
        if obj.member:
            return  '%s: %s' % (obj.member.name, obj.title)
        elif obj.subdomain:
            return  '%s: %s' % (obj.subdomain, obj.title)
        else:
            return obj.title

    def item_links(self, obj):
        return [{'href': obj.link }]

    def item_updated(self, obj):
        return obj.published

    def item_categories(self, obj):
        tags = Tag.objects.get_for_object(obj)
        ret = []
        for tag in tags:
            ret.append({'term': tag.name })
        return ret

    def item_content(self, obj):
        ret = getattr(obj, 'content')
        if not ret:
            ret = obj.title
        return {'type': 'html'}, ret




class AllFeed(atompub.Feed):
    feed_title = 'River for all Djangonauts'
    feed_id = '1338'
    feed_authors = [{'name': 'Djangonauts'}]
    items = BaseFeed.objects.all()[:50]

    def item_id(self, obj):
        return str(obj.id)

    def item_title(self, obj):
        return  '%s: %s' % (obj.member.name, obj.title)

    def item_links(self, obj):
        return [{'href': obj.link }]

    def item_updated(self, obj):
        return obj.published

    def item_content(self, obj):
        ret = getattr(obj, 'content')
        if not ret:
            ret = obj.title
        return {'type': 'html'}, ret
