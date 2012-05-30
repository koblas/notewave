from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

def choice_lookup(value) :
    if not value : return ""

    print value, arg

    return ""

register.filter('choice', choice_lookup)
