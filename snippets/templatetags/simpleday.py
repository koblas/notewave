from django.utils.translation import ugettext as _
from datetime import date
from django.template import defaultfilters
from django import template

register = template.Library()

def simpleday(value, arg=None):
    """
    For date values that are tomorrow, today or yesterday compared to
    present day returns representing string. Otherwise, returns a string
    formatted according to settings.DATE_FORMAT.
    """
    try:
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    delta = value - date.today()
    if delta.days == 0:
        return _(u'today')
    elif delta.days == 1:
        return _(u'tomorrow')
    elif delta.days == -1:
        return _(u'yesterday')
    elif -90 < delta.days and delta.days < 90 :
        return value.strftime('%B ') + "%d" % (value.day)
    return defaultfilters.date(value, arg)
register.filter(simpleday)

def timeuntil(value, arg=None):
    """Formats a date as the time until that date (i.e. "4 days, 6 hours")."""
    from django.utils.timesince import timeuntil
    from datetime import datetime
    if not value:
        return u''
    try:
        return timeuntil(value, arg)
    except (ValueError, TypeError):
        return u''
timeuntil.is_safe = False
