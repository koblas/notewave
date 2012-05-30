from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from snippets.async import AsyncResponse
from ..models import *
from profile.models import UserEmail
from openauth import login, authenticate
from openauth.models import create_user
from openauth.forms.signin import SignInUpForm
from datetime import datetime
from django.core.urlresolvers import reverse

def accepturl(request, id=None) :
    try :
        group = Group.objects.get(invite_id=id)
    except Invite.DoesNotExist :
        group = None

    if not group :
        raise Http404("Invite not found")

    form = None

    if request.method == 'POST' :
        user = None
        if request.user.is_anonymous() :
            form = SignInUpForm(request.POST)
            if form.is_valid() :
                user = form.get_user()
                if not user :
                    from openauth.models import create_user
                    if not UserEmail.objects.filter(email=form.cleaned_data['email'], is_confirmed=True).exists() :
                        user = create_user(request, form.cleaned_data['email'], form.cleaned_data['password'])
                    else :
                        form._errors[''] = "Password mismatch"

                if user :
                    user = authenticate(user=user)
                    login(request, user)
        else :
            user = request.user

        if user :
            try :
                group.add_member(user)
            except :
                pass

            return HttpResponseRedirect(reverse('point:home'))
    else :
        form = SignInUpForm()

    return render_to_response('point/accepturl.html', {
                                        'group' : group,
                                        'form'  : form,
                                    }, context_instance=RequestContext(request))
