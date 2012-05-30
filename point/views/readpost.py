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

def readpost(request, gid=None, pid=None) :
    if request.user.is_anonymous :
        return HttpResponseRedirect(reverse('openauth:signin'))

    error = None

    try :
        group = Group.objects.get(id=gid)
    except Group.DoesNotExist :
        error = 'Group not found'

    post   = None
    member = None
    groups = []

    if not error :
        try :
            post = Post.objects.get(group=group, id=pid)
        except Post.DoesNotExist :
            error = 'Posting not found'

    if not error :
        try :
            member = Member.objects.get(group=group, user=request.user)
            groups = request.user.member_set.all()
        except Member.DoesNotExist :
            error = 'Your not a member of this group'

    return render_to_response('point/readpost.html', {
                            'error'  : error,
                            'post'   : post,
                            'member' : member,
                            'groups' : groups,
                            'group'  : group,
                            'active' : group,
                        }, context_instance=RequestContext(request))
