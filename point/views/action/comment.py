from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *

def comment(request, pid) :
    async = AsyncResponse(request)

    if request.user.is_anonymous() :
        async.need_auth()
    try :
        parent = Post.objects.get(id=pid)
    except Group.DoesNotExist :
        return async.message('message not found')

    try :
        member = Member.objects.get(group=parent.group, user=request.user)
    except Member.DoesNotExist :
        return async.message('your not a member')

    if request.method == 'POST' :
        body = request.POST.get('body', None)

        if body :
            body = body.strip()

            post = Post(user=request.user, group=parent.group, parent=parent, body={ 'text' : body })
            post.save()

            post.email_notify(request, member, post.watchers())

            async.remove('#commentform-%s' % parent.id)
    else :
        async.replace('this', '')
        async.append("#post-%s .comments" % pid, 
                     down_delay=500,
                     template='point/_post_comment.html', 
                     options={
                        'group' : parent.group,
                        'post'  : parent,
                        'member' : member,
                     })
        async.focus('#post-%s form textarea' % pid)

    return async
