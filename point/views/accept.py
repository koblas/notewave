from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from snippets.async import AsyncResponse
from ..models import *
from profile.models import UserEmail
from openauth import login, authenticate
from openauth.models import create_user
from datetime import datetime
from django.core.urlresolvers import reverse

def accept(request, guid=None) :
    try :
        invite = Invite.objects.get(guid=guid)
    except Invite.DoesNotExist :
        invite = None

    if not invite :
        raise Http404("Invite not found")

    member = Member.objects.get(user=invite.user, group=invite.group)

    if request.method == 'POST' :
        invite.accepted_at = datetime.now()
        invite.save()

        uemail = UserEmail.objects.filter(email=invite.email, is_confirmed=True).all()
        if uemail :
            user = uemail[0].user
        else :
            user = create_user(request, invite.email, None, is_confirmed=True)

        # TODO -- send welcome message

        invite.group.add_member(user)

        user = authenticate(user=user)
        login(request, user)

        return HttpResponseRedirect('/')
    else :
        return render_to_response('point/accept.html', {
                                            'member' : member,
                                            'invite' : invite,
                                        }, context_instance=RequestContext(request))
