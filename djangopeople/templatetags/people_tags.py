from django import template
#from template_utils.nodes import ContextUpdatingNode
from django.db import models
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from djangopeople.models import BaseFeed

register = template.Library()

@register.tag()
def feed_for_user(parser, token):
    """
    {% feed_for_user member for service %}
    """
    pass

@register.tag()
def render(parser, token):
    """
Render a ``Item`` by passing it through a snippet template.
::
{% render <item> [using <template>] [as <varname>] %}
A sub-template will be used to render the item. Templates will be searched
in this order:

* The template given with the ``using <template>`` clause, if given.
* ``djangopeople/snippets/<classname>.html``, where ``classname`` is the
name of the specific item class (i.e. ``photo``).
* ``djangopeople/snippets/item.html``.
The template will be passed a context containing:
``item``
The ``BaseFeed`` object
``object``
The actual object (i.e. ``BaseFeed.object``).
The rendered content will be displayed in the template unless the ``as
<varname>`` clause is used to redirect the output into a context variable.
"""
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError("%r tag takes at least one argument" % bits[0])

    item = bits[1]
    args = {}

    # Parse out extra clauses if given
    if len(bits) > 2:
        biter = iter(bits[2:])
        for bit in biter:
            if bit == "using":
                args["using"] = biter.next()
            elif bit == "as":
                args["asvar"] = biter.next()
            else:
                raise template.TemplateSyntaxError("%r tag got an unknown argument: %r" % (bits[0], bit))

    return RenderNode(item, **args)

class RenderNode(template.Node):

    def __init__(self, item, using=None, asvar=None):
        self.item = item
        self.using = using
        self.asvar = asvar

    def render(self, context):
        try:
            item = template.resolve_variable(self.item, context)
        except template.VariableDoesNotExist:
            return ""

        if isinstance(item, BaseFeed):
            object = item.content_object

        # If the item isn't an Item, try to look one up.
        else:
            object = item
            ct = ContentType.objects.get_for_model(item)
            try:
                item = BaseFeed.objects.get(content_type=ct, object_id=object._get_pk_val())
            except Item.DoesNotExist:
                return ""

        # Figure out which templates to use
        template_list = [
            "djangopeople/snippets/%s.html" % item.service.slug,
            "djangopeople/snippets/item.html"
        ]
        if self.using:
            try:
                using = template.resolve_variable(self.using, context)
            except template.VariableDoesNotExist:
                pass
            else:
                template_list.insert(0, using)

        # Render content, and save to self.asvar if requested
        context.push()
        context.update({
            "item" : item,
            "object" : object
        })
        rendered = render_to_string(template_list, context)
        context.pop()
        if self.asvar:
            context[self.asvar] = rendered
            return ""
        else:
            return rendered
