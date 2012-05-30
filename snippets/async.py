import json
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string

def extract_form(html) :
    from lxml import etree

    root = etree.XML(html)

    if root.tag == 'form' :
        form = root
    else :
        form = root.find('form')

    return etree.tostring(form, method='html')

class AsyncResponse(HttpResponse) :
    TYPE_INFO   = 'info'
    TYPE_ERROR  = 'error'

    def __init__(self, request=None, iframe=None) :
        if iframe is None :
            if request is not None :
                self.iframe = request.META.get('CONTENT_TYPE',u"").startswith('multipart/form-data')
            else :
                self.iframe = False
        else :
            self.iframe = iframe

        if self.iframe :
            mt = 'text/html'
        else :
            mt = 'application/json'
        super(AsyncResponse, self).__init__(mimetype=mt)

        self.actions = []
        self.request = request

    def _op(self, op, selector, html, template, text, options, **kwargs) :
        if template :
            if self.request :
                html = render_to_string(template, options, context_instance=RequestContext(self.request))
            else :
                html = render_to_string(template, options)

        if html is not None :
            entry = {'op':op, 'selector':selector, 'html':html}
        elif text :
            entry = {'op':op, 'selector':selector, 'text':text}
        if kwargs :
            entry.update(kwargs)

        self.actions.append(entry)
        return self

    def redirect(self, url) :
        self.actions.append({'op': 'redirect_url', 'url': url})
        return self

    def need_auth(self, msg=None) :
        self.actions.append({'op': 'redirect', 'url': '/openauth/login-dialog', 'message':msg})
        return self

    def message(self, html="", type=TYPE_INFO) :
        self.actions.append({'op' : 'message', 'html' : html, 'type' : type})
        return self

    def dialog(self, title=None, html=None, template=None, options={}, modal=False, dialogClass=None, width=None, height=None) :
        if template :
            if self.request :
                html = render_to_string(template, options, context_instance=RequestContext(self.request))
            else :
                html = render_to_string(template, options)
        self.actions.append({ 
                        'op' : 'dialog', 
                        'title' : title, 
                        'body' : html, 
                        'modal': modal, 
                        'dialogClass': dialogClass,
                        'width' : width,
                        'height' : height,
                    })
        return self

    def history(self, url) :
        return self.actions.append({
                        'op' : 'history',
                        'url' : url,
                    })

    def append(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('append', selector, html, template, text, options, **kwargs)

    def prepend(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('prepend', selector, html, template, text, options, **kwargs)

    def after(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('after', selector, html, template, text, options, **kwargs)

    def before(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('before', selector, html, template, text, options, **kwargs)

    def replace(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('replace', selector, html, template, text, options, **kwargs)

    def replace_with(self, selector, html=None, template=None, text=None, options={}, **kwargs) :
        return self._op('replace_with', selector, html, template, text, options, **kwargs)

    def replace_form(self, selector, html=None, template=None, text=None, options={}) :
        if template :
            if self.request :
                html = render_to_string(template, options, context_instance=RequestContext(self.request))
            else :
                html = render_to_string(template, options)
        if html :
            html = extract_form(html)
            self.actions.append({'op':'replace_with', 'selector':selector, 'html':html})
        elif text :
            self.actions.append({'op':'replace_with', 'selector':selector, 'text':text})
        return self

    def remove(self, selector, duration=0) :
        self.actions.append({'op':'remove', 'selector':selector, 'duration':duration})
        return self

    def dialog_close(self) :
        self.actions.append({'op':'dialog_close'})
        return self

    def attr(self, selector, **kwargs) :
        self.actions.append({'op':'attr', 'selector':selector, 'attr':kwargs})
        return self

    def focus(self, selector) :
        self.actions.append({'op':'focus', 'selector':selector})
        return self

    def set_cookie(self, *args, **kwargs) :
        super(AsyncResponse, self).set_cookie(*args, **kwargs)
        return self

    def track(self, url) :
        self.actions.append({'op':'track', 'url':url})
        return self

    def _get_content(self) :
        s = json.dumps({'actions' : self.actions })
        if self.iframe :
            from cgi import escape
            return '<textarea>\n%s\n</textarea>\n' % escape(s)
        return s

    content = property(_get_content)

    def __iter__(self) :
        self._iterator = iter(self.content)
        return self
