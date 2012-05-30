from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *

def shareinvite(request, gid) :
    async = AsyncResponse(request)

    if request.user.is_anonymous() :
        async.need_auth()

    try :
        group = Group.objects.get(id=gid)
    except Group.DoesNotExist :
        return async.message('group not found')

    try :
        member = Member.objects.get(group=group, user=request.user)
    except Member.DoesNotExist :
        return async.message('your not a member')

    async.dialog(title="Share Via URL", 
                 template="point/_share_dialog.html", 
                 options={
                    'group' : group, 
                    'url'   : request.build_absolute_uri(group.share_url()),
                })

    return async
