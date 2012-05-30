from cStringIO import StringIO
import settings
from snippets.async import AsyncResponse
from wsgiref.handlers import format_date_time
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotModified
from django.contrib.auth.models import User
from django.contrib import messages 
from django.views.decorators import http
from .models import *
from .forms import *
from datetime import datetime
from time import mktime

def home(request) :
    return show(request)

def show(request, username=None, userid=None, display=None) :
    if not username and not userid:
        profiles = UserProfile.objects.all()
        return render_to_response("profile/index.html", {
            'profiles'  : profiles,
        }, context_instance=RequestContext(request))

    if username :
        user = User.objects.get(username=username)
    else :
        user = User.objects.get(id=userid)

    return render_to_response("profile/show.html", {
        'disp_profile'   : user.profile,
    }, context_instance=RequestContext(request))

def settings_about(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    profile = request.user.profile

    if request.method == 'POST' :
        form = ProfileAboutForm(request.POST)
        if form.is_valid() :
            profile.username = form.cleaned_data['username']
            if 'bio' in profile.data :
                profile.data['bio'] = form.cleaned_data['bio']
            profile.save()
            messages.success(request, 'Your changes have been saved.')
    else :
        form = ProfileAboutForm(initial={
            'username' : profile.name(),
            'bio' : profile.data.get('bio',''),
        })

    return render_to_response("profile/settings_about.html", {
        'form'    : form,
    }, context_instance=RequestContext(request))

def settings_photo(request) :
    from PIL import Image
    from cStringIO import StringIO
    from django.core.files.base import ContentFile

    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    if request.method == 'POST' :
        form = ProfilePhotoForm(request.POST, request.FILES)
        if form.is_valid() :
            image = form.cleaned_data['photo']
            profile = request.user.profile

            img = Image.open(ContentFile(image.read()))
            img.thumbnail((480, 480), Image.ANTIALIAS)
            img.convert("RGB")
            fout = StringIO()
            img.save(fout, "PNG", optimize=1)
            fout.seek(0)

            ofile = None
            if profile.image :
                ofile = profile.image.name

            profile.image.save("profile_%s.png" % request.user.id, ContentFile(fout.read()))
            # profile.save() not needed -- save commited

            if ofile :
                # only delete after the save is successful
                profile.image.storage.delete(ofile)
            messages.success(request, 'Your photo has been updated')
    else :
        form = ProfilePhotoForm()

    return render_to_response("profile/settings_photo.html", {
        'form'   : form,
    }, context_instance=RequestContext(request))

def settings_notify(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    form = None
    return render_to_response("profile/settings_notify.html", {
        'form'   : form,
    }, context_instance=RequestContext(request))

def settings_email(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    email_form = None

    if request.method == 'POST' :
        send_email = None

        if 'op_save' in request.POST :
            print "SAVE", request.POST
            try :
                obj = UserEmail.objects.get(user=request.user, email=request.POST.get('addr',None))
                # It exists!
                if obj.is_confirmed :
                    obj.is_primary = True
                    obj.save()
                    request.user.email = obj.email
                    request.user.save()
                    UserEmail.objects.filter(
                        user=request.user, is_primary=True
                    ).exclude(
                        email=obj.email
                    ).update(is_primary=False)
                    messages.success(request, 'Your primary email address has been changed')
                else :
                    messages.error(request, 'Email address is not yet confirmed')
            except UserEmail.DoesNotExist :
                messages.error(request, 'Unknown email address')
        elif 'op_delete' in request.POST :
            try :
                obj = UserEmail.objects.get(user=request.user, email=request.POST.get('addr',None))
                if obj.is_primary :
                    messages.error(request, 'You cannot delete your primary email address')
                else :
                    obj.delete()
                    messages.success(request, 'Your address has been deleted')
            except UserEmail.DoesNotExist :
                messages.error(request, 'Unknown email address')
        elif 'op_resend' in request.POST :
            send_email = request.POST.get('addr', None)
            try :
                obj = UserEmail.objects.get(user=request.user, email=request.POST.get('addr',None))
                if obj.is_confirmed :
                    messages.error(request, 'Address is already confirmed')
                    send_email = None
                else :
                    messages.success(request, 'Confirmation resent')
            except UserEmail.DoesNotExist :
                messages.error(request, 'Unknown email address')
                send_email = None
        else :
            email_form = ProfileEmailAddrForm(request.POST)
            if email_form.is_valid() and email_form.cleaned_data['email'].strip() != '' :
                send_email = email_form.cleaned_data['email']
                    
                try :
                    obj = UserEmail.objects.get(user=request.user, email=email_form.cleaned_data['email'])
                    if obj.is_confirmed :
                        messages.success(request, 'You already have that (%s) email address assoicated' % send_email)
                        send_email = None
                    else :
                        messages.success(request, 'Resending Confirmation')
                    # TODO - should we check to see if another user has this email?
                except UserEmail.DoesNotExist :
                    obj = UserEmail(user=request.user, email=email_form.cleaned_data['email'])
                    obj.key = obj.gen_key()
                    obj.save()
                    messages.success(request, 'A confirmation message has been sent.')
            email_form = None

        if send_email :
            obj.send_confirm(request)

    if email_form is None :
        email_form = ProfileEmailAddrForm()

    email_list = UserEmail.objects.filter(user=request.user)

    return render_to_response("profile/settings_email.html", {
        'email_form'   : email_form,
        'email_list'   : email_list,
    }, context_instance=RequestContext(request))

def confirm_email(request, userid, key) :
    success = False
    try :
        user = User.objects.get(id=userid)
        obj = UserEmail.objects.get(user=user, key=key)
        if obj.is_confirmed :
            pass
        else :
            obj.is_confirmed = True
            obj.save()
            success = True
    except UserEmail.DoesNotExist :
        pass

    return render_to_response("profile/confirm_email.html", {
        'success'      : success,
    }, context_instance=RequestContext(request))

def settings_networks(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    form = None
    return render_to_response("profile/settings_networks.html", {
        'form'      : form,
        'connected' : [ouser.get_service() for ouser in request.user.openuser_set.all()],
        'services'  : settings.OPENAUTH_DATA.keys(),
    }, context_instance=RequestContext(request))

def settings_password(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')
    
    if request.method == 'POST' :
        form = PasswordForm(request.POST)
        if form.is_valid() :
            request.user.set_password(form.cleaned_data['password'])
            request.user.save()
            messages.success(request, 'Your password has been updated')
            form = PasswordForm()
    else :
        form = PasswordForm()
    return render_to_response("profile/settings_password.html", {
        'form'     : form,
        'services' : [ouser.get_service() for ouser in request.user.openuser_set.all()],
    }, context_instance=RequestContext(request))

def action_follow(request, userid) :
    async = AsyncResponse(request).track('/action/follow')

    if request.user.is_anonymous() :
        return async.need_auth()

    user = User.objects.get(id=userid)

    try :
        obj = UserFollow.objects.get(user=request.user, following=user)
        obj.delete()

        return async.message('No longer following: %s ' % user.profile.name()) \
                    .replace('this','Follow') 
    except UserFollow.DoesNotExist :
        obj = UserFollow(user=request.user, following=user)
        obj.save()

        UserNotification.send_follow(user, request.user)

        return async.message('Now following: %s ' % user.profile.name()) \
                    .replace('this','un-Follow') 

def message_read(request, id) :
    async = AsyncResponse(request)

    try :
        if id == 'new_user' :
            request.user.profile.set_sysmsg('new_user', False)
            request.user.profile.save()
            async.remove('#message_new_user', duration=500)
        elif id[0:3] == 'co_' :
            async.remove('#%s_message' % id[3:], duration=500).set_cookie(str(id[3:]), "1")
        else :
            obj = UserNotification.objects.get(id=id, user=request.user)
            obj.is_read = True
            obj.save()

            if request.user.profile.notifications().count() == 0 :
                async.remove('#message_box', duration=500)
            else :
                async.remove('this', duration=500)
    except UserNotification.DoesNotExist :
        pass

    return async

def connect(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    site = request.GET.get('site', None)

    async = AsyncResponse(request) 

    if site : 
        async.replace_with('#%s_connect' % site, '<span id="%s_connect">Connected</span>' % site)
    
    return async

def signup_profile(request) :
    if request.user.is_anonymous() :
        raise Http404('must be logged in')

    profile = request.user.profile

    if request.method == 'POST' :
        form = ProfileSignupForm(request.POST)
        if form.is_valid() :
            if 'username' in form.cleaned_data :
                profile.username = form.cleaned_data['username']
            profile.data['bio'] = form.cleaned_data['bio']
            profile.save()
            return HttpResponseRedirect('/')
    else :
        form = ProfileSignupForm()
        #form = ProfileSignupForm(initial={
        #    'username' : profile.name(),
        #    'bio'      : profile.data.get('bio',''),
        #})

    return render_to_response("profile/signup.html", {
        'form'    : form,
    }, context_instance=RequestContext(request))
