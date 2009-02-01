from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy

from pages import settings
from pages.models import Page, Content, tagging

class PageForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(),
        help_text=_('The default title'))
    slug = forms.CharField(widget=forms.TextInput(),
        help_text=_('The part of the title that is used in permalinks'))
    language = forms.ChoiceField(choices=settings.PAGE_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    template = forms.ChoiceField(choices=settings.PAGE_TEMPLATES, required=False,
        help_text=_('The template used to render the content.'))

    if tagging:
        from tagging.forms import TagField
        from pages.admin.widgets import AutoCompleteTagInput
        tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        if settings.PAGE_UNIQUE_SLUG_REQUIRED:
            if self.instance.id:
                if Content.objects.exclude(page=self.instance).filter(body=slug, type="slug").count():
                    raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
            elif Content.objects.filter(body=slug, type="slug").count():
                raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
        return slug
