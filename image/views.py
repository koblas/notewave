from cStringIO import StringIO
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotModified
from wsgiref.handlers import format_date_time
from django.views.decorators import http
from datetime import datetime
from time import mktime

#
#
def import_class(name) :
    from django.utils.importlib import import_module

    parts = name.split('.')
    nm = '.'.join(parts[0:-1])
    module = import_module(nm)

    try :
        return getattr(module, parts[-1])
    except :
        return None

MIN_DATE = datetime(2001, 1, 1)
def _latest_version(request, **kwargs):
    return MIN_DATE

@http.last_modified(_latest_version)
def icon(request, mod=None, uid=None, size="32x32", fmt="PNG") :
    from hashlib import sha1
    import settings
    from .identicon import render_identicon

    cls = import_class(mod)

    rawimage = None
    if cls :
        rawimage = cls.icon_image(uid)

    if fmt  : fmt = fmt.lower()
    if size : 
        w, h = size.split('x')
        w = int(w)
        h = int(h)
    else :
        w, h = 32, 32

    if rawimage :
        from PIL import Image

        thumb = Image.open(rawimage.file)
        image = Image.new("RGB", (w, h), (255,255,255))

        if False :
            if thumb.size[0] > thumb.size[1] :
                scale = w / float(thumb.size[0])
            else :
                scale = h / float(thumb.size[1]) 
        else :  
            if thumb.size[0] < thumb.size[1] :
                scale = w / float(thumb.size[0])
            else :
                scale = h / float(thumb.size[1]) 

        thumb = thumb.resize((thumb.size[0] * scale, thumb.size[1] * scale), Image.ANTIALIAS)
        dw = (w - thumb.size[0]) / 2
        dh = (h - thumb.size[1]) / 2
        image.paste(thumb, (dw, dh))

        fout = StringIO()
    else :
        s = sha1()
        s.update(settings.SECRET_KEY)

        s.update(mod)
        s.update(uid)

        v = s.hexdigest()

        image = render_identicon(int(v[0:16], 16), w / 3)

    ofd = StringIO()
    if fmt == 'gif' :
        mimetype = "image/gif"
        image.save(ofd, "GIF")
    elif fmt == 'jpg' :
        mimetype = "image/jpeg"
        image.save(ofd, "JPG")
    else :
        mimetype = "image/png"
        image.save(ofd, "PNG")

    nowtuple = datetime.now().timetuple()
    data = ofd.getvalue()

    response = HttpResponse(content=data, mimetype=mimetype)
    response['Content-Length'] = len(data)
    response['Content-Type']   = mimetype
    response['Cache-Control']  = 'public'
    response['Expires']        = format_date_time(mktime(nowtuple) + 30 * 24*60*60)

    # match the code in http.last_modified -- since it does an "==" on the timestamps
    from calendar import timegm
    from email.Utils import formatdate
    response['Last-Modified']  = formatdate(timegm(MIN_DATE.utctimetuple()))[:26] + 'GMT'

    return response
