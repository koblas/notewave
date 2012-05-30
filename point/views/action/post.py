from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *
import re

def post(request, gid) :
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
        body = request.POST.get('body', None)
        file = None

        if 'attachment' in request.FILES :
            file = request.FILES['attachment']

        if body or file :
            error = None

            body = body.strip()
            icount = 0
            if file :
                icount = 1

            post = Post(user=request.user, group=group, body={ 'text' : body })
            post.save(notify=False)

            if file :
                ipost = post.add_image(file.read())
                if not ipost :
                    error = "Unable to interpret image"
                    post.delete()
                else :
                    post.save()

            if not error :
                post.notify()

                post.email_notify(request, member, post.watchers())

                async.replace_form('#main_body form.group_post',
                       template='point/_group_feed.html',
                       options = {
                        'posts' : [],
                        'group' : post.group,
                        'active' : post.group,
                    })
            else :
                async.message(error)

                async.replace_form('#main_body form.group_post',
                       template='point/_group_feed.html',
                       options = {
                        'posts' : [],
                        'group' : post.group,
                        'active' : post.group,
                        'form'   : {
                                'body' : body,
                            }
                    })
    else :
        async.message("Bad method")

    return async
