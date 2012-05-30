from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *
from ...forms.create import CreateGroupForm

def groupsettings(request, gid) :
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

    if 'notify' in request.GET :
        if member.notify_on_post :
            member.notify_on_post = False
        else :
            member.notify_on_post = True
        member.save()

    async.replace_with('#group_settings', 
                template="point/_group_settings.html",
                options = {
                    'group'   : group,
                    'member'  : member,
                    'visible' : True,
                })

    return async
