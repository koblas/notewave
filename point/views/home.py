from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from ..forms.login import SignInForm

def home(request, force=False) :
    if request.user.is_anonymous() or force :
        return render_to_response('point/home.html', {
                                            'form' : SignInForm(),
                                        }, context_instance=RequestContext(request))

    if not request.user.is_confirmed :
        return HttpResponseRedirect(reverse('openauth:signup_confirm'))

    if request.user.member_set.count() == 0 :
        from ..models import User, Group
        user  = User.objects.get(id=1)

        demogroup = None
        l = Group.objects.filter(created_by=user, title='Demo Group').order_by('created_at')[:1]
        if l :
            demogroup = l[0]
            if demogroup.member_set.count() > 50 :
                demogroup = None
        
        if not demogroup :
            demogroup = Group(created_by=user, title='Demo Group')
            demogroup.save()

        member = demogroup.add_member(request.user)

    posts = []
    for member in request.user.member_set.all() :
        for post in member.group.root_post_set()[0:5] :
            posts.append(post)

    posts = sorted(posts, key=lambda post : post.created_at, reverse=True)

    return render_to_response('point/dashboard.html', {
                                            'posts' : posts[:20],
                                        }, context_instance=RequestContext(request))
