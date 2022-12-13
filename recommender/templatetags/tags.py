from django import template

register = template.Library()

@register.filter
def get_item(dict, key):
    return dict.get(key)