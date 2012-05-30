from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.template import RequestContext, Context

def email_template(subject="", html=None, text=None, rcpt=[], sender="help@notewave.com", context_instance=None, fail_silently=True) :
    if not context_instance :
        context_instance = Context()

    if text :
        body_text = render_to_string(text, context_instance)
    else :
        body_text = ""
    msg = EmailMultiAlternatives(subject, body_text, sender, rcpt)

    if html :
        body_html = render_to_string(html, context_instance)
        msg.attach_alternative(body_html, 'text/html')

    try :
        msg.send(fail_silently=fail_silently)
    except Exception, e :
        print e
