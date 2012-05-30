from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *

def like(request, pid) :
    async = AsyncResponse(request)

    if request.user.is_anonymous() :
        async.need_auth()
    try :
        post = Post.objects.get(id=pid)
    except Group.DoesNotExist :
        return async.message('message not found')

    try :
        member = Member.objects.get(group=post.group, user=request.user)
    except Member.DoesNotExist :
        return async.message('your not a member')

    from django.db.models import F

    created = False
    try :
        like = Like.objects.get(user=request.user, post=post)
        post.likes = F('likes') - 1
        like.delete()
    except Like.DoesNotExist :
        created = True
        like = Like(user=request.user, post=post)
        post.likes = F('likes') + 1
        like.save()

    post.save()

    if created :
        async.replace('this', 'Unlike')
    else :
        async.replace('this', 'Like')

    return async
