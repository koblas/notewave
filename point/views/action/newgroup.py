from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *
from ...forms.create import CreateGroupForm

def newgroup(request) :
    async = AsyncResponse(request)

    if request.user.is_anonymous() :
        async.need_auth()

    if not request.user.is_email_confirmed :
        async.dialog(title="Need Confirmation", 
                     template="point/_need_confirm.html", 
                     options={
                        })
        return async

    if request.method == 'POST' :
        form = CreateGroupForm(request.POST)
        if form.is_valid() :
            name = form.cleaned_data['name']

            group = Group(created_by=request.user, title=name)
            group.save()

            member = group.add_member(request.user)

            #async.replace_with('#group_list_box', 
            #              template="point/_group_list.html", 
            #              options={
            #                'active' : group,
            #                'groups' : request.user.member_set.all()
            #            })

            async.dialog_close()

            posts = group.root_post_set()

            async.replace('#main_body', 
                      template='point/_group_feed.html',
                      options = {
                        'has_more' : False,
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
        else :
            async.replace_form('this', 
                               template="point/_create_dialog.html", 
                               options={
                                    'form' : form,
                               })

    else :
        form = CreateGroupForm()
        async.dialog(title="Create a Group", 
                     template="point/_create_dialog.html", 
                     options={
                            'form' : form,
                        })

    return async
