from django.template import RequestContext
from snippets.async import AsyncResponse
from ...models import *
from ...forms.invite import InviteGroupForm

def invite(request, gid) :
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
        form = InviteGroupForm(request.POST)
        if form.is_valid() :
            email = form.cleaned_data['email']

            invite = Invite(group=group, user=request.user, email=email)
            try :
                invite.save()
            except :
                from datetime import datetime
                invite = Invite.objects.get(group=group, user=request.user, email=email)
                invite.created_at = datetime.now()
                invite.save()
            _send_invite(request, invite)

            async.dialog_close()
        else :
            async.replace_form('this', 
                               template="point/_invite_dialog.html", 
                               options={
                                    'form' : form,
                                    'group' : group,
                               })

    else :
        form = InviteGroupForm()
        async.dialog(title="Invite Members", 
                     template="point/_invite_dialog.html", 
                     options={
                            'form' : form,
                            'group' : group,
                        })

    return async

def _send_invite(request, invite) :
    from django.core.mail import EmailMultiAlternatives
    from django.core.urlresolvers import reverse
    from django.template.loader import render_to_string
    from django.template import RequestContext, Context

    url = request.build_absolute_uri(reverse('point:accept', kwargs={'guid':invite.guid}))

    body_text = render_to_string('point/_email_invite.txt', RequestContext(request, {
                'invite' : invite,
                'addr' : invite.email,
                'name' : invite.user.profile.name(),
                'url'  : url,
            }))
    body_html = render_to_string('point/_email_invite.html', RequestContext(request, {
                'invite' : invite,
                'addr' : invite.email,
                'name' : invite.user.profile.name(),
                'url'  : url,
            }))

    msg = EmailMultiAlternatives('Notewave | You\'ve been invited to: %s' % invite.group.title, body_text, 'invite@notewave.com', [invite.email])
    msg.attach_alternative(body_html, 'text/html')
    msg.send()
