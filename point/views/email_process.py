from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from snippets.async import AsyncResponse
from ..models import *
from profile.models import UserEmail
from openauth import login, authenticate
from openauth.models import create_user
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
from cStringIO import StringIO

import email

@csrf_exempt
def processemail(request) :
    if request.method != 'POST' or 'body' not in request.POST :
        return HttpResponse('-Malformed')

    rcpt = request.POST['rcpt']
    msg  = email.message_from_string(str(request.POST['body']))

    if not rcpt :
        hdr_to = msg.get('to')
        rcpt   = email.utils.parseaddr(hdr_to)[1]

    hdr_from = msg.get('from')
    hdr_from = email.utils.parseaddr(hdr_from)[1]

    #
    #  Tear appart email message
    #
    images    = []
    bodyparts = []
    if msg.is_multipart() :
        for part in msg.get_payload() :
            cmain = part.get_content_maintype()
            csub  = part.get_content_subtype()

            if cmain == 'text' :
                if msg.get_content_subtype() == 'alternative'  :
                    if csub == 'plain' :
                        bodyparts = [part]
                    elif csub == 'html' :
                        bodyparts = [part]
                elif msg.get_content_subtype() == 'mixed'  :
                    bodyparts.append(part)
            elif cmain == 'image' :
                images.append(part)

    else :
        cmain = msg.get_content_maintype()
        csub  = msg.get_content_subtype()

        part  = msg

        if cmain == 'text' :
            if msg.get_content_subtype() == 'alternative'  :
                if csub == 'plain' :
                    bodyparts = [part]
                elif csub == 'html' :
                    bodyparts = [part]
            elif msg.get_content_subtype() == 'mixed'  :
                bodyparts.append(part)
        elif cmain == 'image' :
            images.append(part)

    #
    #  Convert to happy data
    #
    body = ""
    for p in bodyparts :
        if p.get_content_subtype() == 'text' :
            body += p.get_payload(decode=True)
        else :
            body += p.get_payload(decode=True)
    body = body.strip()

    iout = [StringIO(image.get_payload(decode=True)) for image in images]

    #
    #  Now do the next bit of work...
    #
    try :
        ue = UserEmail.objects.get(email=hdr_from, is_confirmed=True)
        user = ue.user
    except :
        return HttpResponse('-UserNotFound')

    eaddr = rcpt.split('@')[0]
    try :
        group = Group.objects.get(eaddr=eaddr)
    except :
        return HttpResponse('-GroupNotFound: %s' % eaddr)

    if not Member.objects.filter(group=group, user=user).exists() :
        return HttpResponse('-NotMember')

    if user and (body or iout) :
        post = Post(user=user, group=group, body={ 'text' : body })
        post.save(notify=False)

        if iout :
            for ofd in iout :
                post.add_image(ofd.getvalue())
            post.save()

        post.notify()

    return HttpResponse('+Ok')
