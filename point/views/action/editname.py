from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *
from ...forms.username import EditNameForm

def editname(request, gid) :
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

    if request.method == 'POST' :
        form = EditNameForm(request.POST)
        if form.is_valid() :
            name = form.cleaned_data['name']

            member.username = name
            member.save()

            async.replace('.sidebar', 
                          template="point/_group_sidebar.html", 
                          options={
                            'member' : member,
                            'groups' : request.user.member_set.all(),
                            'active' : group,
                        })

            async.dialog_close()
        else :
            async.replace_form('this', 
                               template="point/_edit_username.html", 
                               options={
                                    'form' : form,
                                    'group' : group,
                               })

    else :
        form = EditNameForm()
        async.dialog(title="Create a Group", 
                     template="point/_edit_username.html", 
                     options={
                            'form' : form,
                            'group' : group,
                        })

    return async
