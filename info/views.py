# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import loader, RequestContext

def dispatch(request, page=None) :
    parts = [p for p in request.path.split('/') if p]
    body_tmpl = None
    while parts and not body_tmpl :
        try :
            body_tmpl = loader.get_template('info/%s.html' % '_'.join(parts))
        except Exception, e:
            parts.pop(0)
            continue

    if not body_tmpl :
        raise Http404()

    parts = [p for p in request.path.split('/') if p]
    page_tmpl = None
    while parts and not page_tmpl :
        try :
            page_tmpl = loader.get_template('info/_%s.html' % '_'.join(parts))
        except Exception, e:
            parts.pop(-1)
            continue

    if not page_tmpl :
        page_tmpl = loader.get_template('info/_default.html')

    ctx = RequestContext(request)

    return HttpResponse(page_tmpl.render(RequestContext(request, {
                                                'body' : body_tmpl.render(ctx),
                                                'page' : page,
                                                'request' : request,
                                            })))

def support_dialog(request) :
    from crowd.async import AsyncRequest

    async = AsyncRequest(request)

    async.dialog(title="Support Request")

    return async
