from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name="class_for_number")
@stringfilter
def class_for_number(value) :
    if not value : return ""
    v = int(value)
    if v > 10000 : return "big_number"
    if v > 1000  : return "medium_number"
    if v < 0     : return "negative_number"
    return ""

@register.filter(name="human_short")
@stringfilter
def human_short(value) :
    if not value : return "0"
    v = int(value)
    if v < 1000 :   return value
    if v < 1000000 : return "%.01fK" % (v / 1000.0)
    return "%0.01fM" % (v / 1000000.0)

@register.filter(name="cleanhtml")
@stringfilter
def cleanhtml(value) :
    from ..html import clean_html
    from django.utils.safestring import mark_safe
    return mark_safe(clean_html(value))

@register.filter('choice')
def choice_lookup(value, arg) :
    if not value : return ""

    try :
        if hasattr(value, 'items') :
            for k, v in value.items() :
                if arg == k : return v
        for k,v in value :
            if arg == k : return v
    except :
        pass
    return ""

@register.filter('index')
def index_lookup(value, arg) :
    if not value : return ""

    try :
        return value[int(arg)]
    except :
        pass
    return ""

@register.filter('prettyurl')
def pretty_url(value, tlen=40) :
    if not value : return ""

    res = []

    try :
        from urlparse import urlparse
        parts = urlparse(value)

        if parts.scheme not in ('http', 'https') :
            return value
        res.append(parts.netloc)

        remain = tlen - len(parts.netloc)

        plist = parts.path.split('/')[1:]
        addslash = False
        if plist and not plist[-1] :
            addslash = True
            if len(plist) > 1 :
                plist = plist[0:-1]

        if len(plist) > 1 :
            if len(plist) != 2 :
                remain -= 3
                res.append('...')
            else :
                remain -= len(plist[-2])
                res.append(plist[-2])

        if remain > len(plist[-1]) :
            res.append(plist[-1])
        else :
            res.append("%s..." % plist[-1][0:remain-3])
        if addslash and res[-1] != '' :
            res.append('')

        if remain > 4 and parts.query :
            res[-1] = "%s?..." % res[-1]

        return '/'.join(res)
    except Exception, e:
        raise e
        pass
    if res :
        return '/'.join(res)
    return value
