from django import template
from django.forms import BoundField

register = template.Library()


@register.inclusion_tag('partials/form_field.html')
def render_field(field: BoundField) -> dict:
    return {'field': field}
