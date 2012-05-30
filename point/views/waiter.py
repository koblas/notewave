from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from snippets.async import AsyncResponse
from ..models import Group, Member, Post
import json
import time 
import tornado.web
from django_tornado.decorator import asynchronous

@asynchronous
def waiter(request, handler) :
    response = {}

    if request.user.is_anonymous() :
        raise Http404("not logged in")

    def on_new_messages(group, post) :
        if handler.request.connection.stream.closed():
            return

        async = AsyncResponse()
        if not post or post.user != request.user :
            try :
                member = Member.objects.get(group=group, user=request.user)

                async.replace('#group-%s .count' % group.id, member.new_count())
            except Exception, e :
                print 'waiter exception - ', e

        #
        #
        #
        if post :
            if post.parent :
                async.append('#post-%s .comments' % post.parent.id,
                   template='point/_post_comment_line.html',
                   down_delay=500,
                   options = {
                    'comment' : post,
                })
            else :
                async.prepend('#feed-%s' % post.group.id,
                   template='point/_post_line.html',
                   down_delay=500,
                   options = {
                    'post' : post,
                    'active' : post.group,
                })

        #
        #
        #
        s = str(async.content)
        handler.finish(s)


    for member in request.user.member_set.all() :
        member.group.cb_register(on_new_messages)
