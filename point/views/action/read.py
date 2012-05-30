from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from snippets.async import AsyncResponse
from datetime import datetime
from ...models import *
from django.core.urlresolvers import reverse

def read(request, gid, offset=0) :
    error = None

    if not request.is_ajax() :
        if request.user.is_anonymous() :
            return HttpResponseRedirect(reverse('openauth:signin'))
    else :
        async = AsyncResponse(request)

        if request.user.is_anonymous() :
            return async.need_auth()

    try :
        group = Group.objects.get(id=gid)
    except Group.DoesNotExist :
        error = 'group not found'

    try :
        member = Member.objects.get(group=group, user=request.user)
    except Member.DoesNotExist :
        error = 'your not a member'

    if error :
        if request.is_ajax() :
            return async.message(error)
        else :
            raise Http404(error)

    member.lastread_at = datetime.now()
    member.save()

    count = 10
    offset = int(offset)
    posts = group.root_post_set()[offset:offset+count+1]

    has_more = len(posts) == count+1

    if not request.is_ajax() :
        return render_to_response('point/dashboard.html', {
                                            'posts' : posts,
                                            'group' : group,
                                            'active' : group,
                                        }, context_instance=RequestContext(request))

    if offset != 0 :
        for post in posts :
            async.append('#feed-%d' % group.id, 
                              template="point/_post_line.html",
                              options = {
                                'post' : post,
                                'group' : group,
                                'active' : group,
                              })
        if has_more :
            async.attr('#more_button', href="#!%s" % reverse('point:more', args=[group.id, offset+count]))
        else :
            async.remove('#more_button')
    else :
        async.replace('#main_body', 
                  template='point/_group_feed.html',
                  options = {
                    'has_more' : has_more,
                    'group'  : group,
                    'posts'  : posts,
                    'active' : group,
                  })

        async.replace('#content .sidebar', 
                          template="point/_group_sidebar.html", 
                          options={
                            'member' : member,
                            'groups' : request.user.member_set.all(),
                            'active' : group,
                        })

    async.history("/read/%d" % group.id)
    return async

