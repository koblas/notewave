import uuid, base64, urlparse, json

from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, QueryDict, Http404
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse

from django.shortcuts import render_to_response
from django.template.loader import render_to_string

from oauth import oauth, client
from openid.consumer import consumer
from openid.store import memstore
import openid.message
from openid import association, oidutil
from openid.extensions import sreg, ax

from models import OpenUser, OAuthStore, User, OPENID_SERVICES, PasswordRecovery
import util
from . import login, authenticate, logout
from snippets.async import AsyncResponse

#import ybrowserauth
import settings

#
#
#
class OAuthCookieSession(object) :
    """Total glue to make things look like a cookie without a full django.session
        Not USED!
    """

    def __init__(self, request) :
        self._dict = {}

    def __getitem__(self, name) :
        print "GET __getitem__ ITEM", name
        return self._dict[name]

    def get(self, name, default=None) :
        print "GET 'get' ITEM", name
        return self._dict.get(name, default)

    def __setitem__(self, name, value) :
        print "SET ITEM", name, value
        self._dict[name] = value

    def __delitem__(self, name) :
        print "DEL ITEM", name
        del self._dict[name]

#
#  CURL Fetcher is broken
#
from openid import fetchers
from models import GENERATED_USERBASE
fetchers.setDefaultFetcher(fetchers.Urllib2Fetcher())

##
#
#
#
attrs_dict = {'width':'100%'}
class DetailsForm(forms.Form) :
    username = forms.RegexField(regex=r'^\w+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_(u'username'),
                                required=False)
    display = forms.CharField(max_length=70,
                               widget=forms.TextInput(attrs=attrs_dict),
                               label=_(u'display name'), 
                               required=False)
    email = forms.EmailField(widget=forms.TextInput(attrs=attrs_dict),
                             label=_(u'email address'), 
                             required=False)

    def __init__(self, user, *args, **kwargs) :
        self._user = user
        super(DetailsForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        """
        from django.core import validators
        uname = self.cleaned_data.get('username', '')

        # Not generated an not provided, don't change it
        if self._user.username.find(GENERATED_USERBASE) == -1 and uname in validators.EMPTY_VALUES :
            return self._user.username

        if uname == self._user.username :
            return uname

        if uname in validators.EMPTY_VALUES :
            print "RAISE 3"
            raise ValidationError(self.username.error_messages['required'])

        try:
            user = User.objects.get(username__iexact=uname)
        except User.DoesNotExist:
            return uname
        raise forms.ValidationError(_(u'This username is already taken. Please choose another.'))

    def clean_email(self) :
        from django.core import validators

        email = self.cleaned_data.get('email', '')

        # None provided, existing one, use the existing
        if self._user.email not in validators.EMPTY_VALUES and email in validators.EMPTY_VALUES :
            return self._user.email

        if not self._user.email and self.cleaned_data['email'] in validators.EMPTY_VALUES :
            print "RAISE 2"
            raise ValidationError(self.email.error_messages['required'])
        if self._user.email :
            return self._user.email
        return self.cleaned_data['email']

    def clean_display(self) :
        from django.core import validators
        if not self._user.email and self.cleaned_data['display'] in validators.EMPTY_VALUES :
            print "RAISE"
            raise ValidationError(self.display.error_messages['required'])
        if self._user.get_full_name() :
            return self._user.get_full_name()
        return self.cleaned_data['display']

#
# Pinged by facebok when a user adds.
#
def facebook_authenticate_add(request) :
    return HttpResponse('ok')

#
# Pinged by facebok when a user removes.
#
def facebook_authenticate_remove(request) :
    return HttpResponse('ok')

#
# OpenID handling
#
def xrds(request) :
    return_to = request.build_absolute_uri(reverse('openauth:callback', args=[""]))

    xml = ''
    xml += '<?xml version="1.0" encoding="UTF-8"?>'
    xml += '<xrds:XRDS xmlns:xrds="xri://$xrds" xmlns:openid="http://openid.net/xmlns/1.0"  xmlns="xri://$xrd*($v*2.0)">'
    xml += '<XRD>'
    xml += '<Service>'
    xml += '<Type>http://specs.openid.net/auth/2.0/return_to</Type>'
    xml += '<URI>%s</URI>' % return_to
    xml += '</Service>'
    xml += '</XRD>'
    xml += '</xrds:XRDS>'

    return HttpResponse(xml, mimetype="application/xrds+xml")

def open_prompt(request, site=None, popup=False) :
    """ Redirect the user to the approprate OAuth provider to get credientals """

    c = consumer.Consumer(request.session, util.OpenIDStore())
    c.setAssociationPreference([('HMAC-SHA1', 'no-encryption')])

    if popup : 
        return_to = request.build_absolute_uri(reverse('openauth:pop_callback', kwargs={'site':site}))
    else :
        return_to = request.build_absolute_uri(reverse('openauth:callback', kwargs={'site':site}))

    if site not in settings.OPENAUTH_DATA :
        raise Http404("Unknown OAuth service %s" % site)

    if site == 'google' :
        auth_request = c.begin('https://www.google.com/accounts/o8/id')

        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'mode', 'fetch_request')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'required', 'email,firstname,lastname')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'type.email', 'http://schema.openid.net/contact/email')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'type.firstname', 'http://axschema.org/namePerson/first')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'type.lastname', 'http://axschema.org/namePerson/last')

        auth_request.addExtensionArg('http://specs.openid.net/extensions/oauth/1.0', 'consumer', settings.OPENAUTH_DATA[site]['key'])
        auth_request.addExtensionArg('http://specs.openid.net/extensions/oauth/1.0', 'scope', 'http://www.google.com/m8/feeds')

        parts     = list(urlparse.urlparse(return_to))
        realm     = urlparse.urlunparse(parts[0:2] + [''] * 4)

        url = auth_request.redirectURL(realm, return_to)
    elif site == 'yahoo' :
        auth_request = c.begin('http://open.login.yahooapis.com/openid20/www.yahoo.com/xrds')
        auth_request.message.namespaces.addAlias('http://specs.openid.net/extensions/oauth/1.0', 'oauth')
        auth_request.message.setArg(openid.message.OPENID2_NS, 'identity', 'http://specs.openid.net/auth/2.0/identifier_select')

        auth_request.addExtensionArg('http://specs.openid.net/extensions/oauth/1.0', 'consumer', settings.OPENAUTH_DATA[site]['key'])
        parts     = list(urlparse.urlparse(return_to))
        realm     = urlparse.urlunparse(parts[0:2] + [''] * 4)

        url = auth_request.redirectURL(realm, return_to)
    elif site == 'facebook' :
        import urllib

        #return render_to_response('openauth/facebook_r.html', {
        #                                            'apikey' : settings.OPENAUTH_DATA[site]['key']
        #                                    }, context_instance=RequestContext(request))

        if 'code' in request.GET :
            url = 'https://graph.facebook.com/oauth/access_token?%s' % urllib.urlencode({
                                'client_id' : settings.OPENAUTH_DATA[site]['appid'],
                                'redirect_uri' : return_to,
                                'code' : request.GET['code'],
                                'client_secret' : settings.OPENAUTH_DATA[site]['secret'],
                        })
        else :
            url = 'https://graph.facebook.com/oauth/authorize?%s' % urllib.urlencode({
                                'client_id' : settings.OPENAUTH_DATA[site]['appid'],
                                'redirect_uri' : return_to,
                                'scope' : 'email,user_status',
                        })

    elif site in OPENID_SERVICES :
        try :
            c = OpenUser.client_for(site)
        except OpenUser.NoProvider :
            raise Http404("Unknown OAuth service %s" % site)
        token = c.get_request_token(return_to)

        #print 'TOKEN = ', token['oauth_token']
        #print 'SECRET = ', token['oauth_token_secret']
        cache.set('oauth_token_%s' % token['oauth_token'], token['oauth_token_secret'])
        url = c.get_authorize_url(token['oauth_token'], callback=return_to)
    else :
        raise Http404("Unknown OAuth service")

    return HttpResponseRedirect(url)

def open_callback(request, site=None, popup=False, nexturl='/') :
    """ After 3rd party service has completed """

    try :
        doneurl = reverse('registration_complete', args=[site])
    except :
        doneurl = '/'

    #
    #
    #
    token         = None
    didReg        = False
    identity      = None
    email         = None
    fname         = None
    lname         = None
    auth_response = None
    merge_user    = None
    open_user_data = None

    if not request.user.is_anonymous() :
        merge_user = request.user

    if popup : 
        return_to = request.build_absolute_uri(reverse('openauth:pop_callback', kwargs={'site':site}))
    else :
        return_to = request.build_absolute_uri(reverse('openauth:callback', kwargs={'site':site}))

    #
    #  Legacy ... not sure if it every happens anymore should probably DEBUG
    #
    if 'oauth_token' not in request.GET and 'openid.mode' not in request.GET and site not in ('facebook', 'fboauth') :
        print "!! Sending back xrds document -- WHY?"
        return xrds()
        
    #
    #
    #
    if site == 'facebook' :
        if 'code' in request.GET :
            import urllib, urllib2

            return_to = request.build_absolute_uri(reverse('openauth:pop_callback', kwargs={'site':site}))

            url = 'https://graph.facebook.com/oauth/access_token?%s' % urllib.urlencode({
                                'client_id'     : settings.OPENAUTH_DATA[site]['appid'],
                                'redirect_uri'  : return_to,
                                'code'          : request.GET['code'],
                                'client_secret' : settings.OPENAUTH_DATA[site]['secret'],
                        })

            print "OPENING", url
            try :
                req = urllib2.Request(url)
                response = urllib2.urlopen(req)
            except Exception,e  :
                print "EXCEPTION",e
            else :
                data = response.read()

                vals = dict([param.split('=') for param in data.split('&')])

            from facebook2 import GraphAPI

            graph = GraphAPI(vals['access_token'])

            profile = graph.get_object('me')

            open_user_data = profile

            email = profile['email']
            fname = profile['first_name']
            lname = profile['last_name']

            identity = 'facebook:%s' % profile['id']

            #token = {
            #    'oauth_token'        : facebook.auth_token or '',
            #    'oauth_token_secret' : facebook.session_key,
            #    'expires'            : facebook.session_key_expires,
            #}
    elif 'oauth_token' in request.GET :
        #
        # OAuth Login (LinkedIn)
        #
        if site not in OPENID_SERVICES :
            return HttpResponse('Invalid site')

        tok = request.GET['oauth_token']
        tok_secret = cache.get('oauth_token_%s' % tok, None)

        #print "OAUTH Login"

        try :
            c = OpenUser.client_for(site, oauth_token=tok, oauth_token_secret=tok_secret)
        except OpenUser.NoProvider :
            raise Http404("No provider for serivce %s" % site)

        if 'oauth_verifier' in request.GET :
            token = c.get_access_token(token=tok, verifier=request.GET['oauth_verifier'])
        else :
            token = c.get_access_token(token=tok)

        identity = "oauth:%s:%s" % ( site, token['oauth_token'] )
    else :
        #print "OpenID Login"
        #for k, v in request.GET.items() : print k, v

        #
        #  OpenID Login (Google for Example)
        #
        if request.GET.get('openid.mode', None) == 'cancel' or request.GET.get('openid.mode', None) != 'id_res' :
            if popup : 
                return HttpResponse(loader.get_template('openauth/popup_close.html').render(RequestContext(request, { 
                                            'error'  : "Authentication declined", 
                                            'service': site,
                                    })))
            return render_to_response('openauth/decline.html', {
                                            }, context_instance=RequestContext(request))

        c = consumer.Consumer(request.session, util.OpenIDStore())
        c.setAssociationPreference([('HMAC-SHA1', 'no-encryption')])

        auth_response = c.complete(request.GET, return_to)

        if isinstance(auth_response, consumer.FailureResponse) :
            if popup : 
                return HttpResponse(loader.get_template('openauth/popup_close.html').render(RequestContext(request, { 
                                            'error'  : "Error from %s - %s" (site, auth_reponse), 
                                            'service': site,
                                    })))
            return render_to_response('openauth/decline.html', {
                                                'auth_response' : auth_response,
                                            }, context_instance=RequestContext(request))
    
        identity = auth_response.getSigned(openid.message.OPENID2_NS, 'identity', None)

        em = auth_response.extensionResponse('http://schema.openid.net/contact/email', True)
        if not em or len(em) == 0 :
            em = auth_response.extensionResponse('http://openid.net/srv/ax/1.0', True)
            email = em.get('value.email', None)

            open_user_data = {'email':email}

    #
    #  Now that we have an Internal identiy for this user, see if they already exist
    #
    try :
        oiuser = OpenUser.objects.get(openid=identity, source='openid')
    except OpenUser.DoesNotExist :
        oiuser = None

    #
    #  If the existing user and the authenticated user are the same, do nothing
    #
    if oiuser and merge_user == oiuser.user :  
        merge_user = None

    response = None
    message  = None
    user     = None

    if oiuser :
        message = None

        if not oiuser.user.is_active :
            message = 'Account disabled'
        if request.user.is_active and request.user != oiuser.user :
            message = 'Account is already associated with another account, you should login instead.'

        if not message  :
            user = authenticate(user=oiuser.user)
            login(request, user)

        if popup : 
            return HttpResponse(loader.get_template('openauth/popup_close.html').render(RequestContext(request, { 
                                        'error'  :  message, 
                                        'service': site,
                                })))
        return HttpResponse(message)

        # TODO - A disalbed (!is_active) user is associated... ??
    else :
        if request.user.is_anonymous() :
            if popup :
                return HttpResponse(loader.get_template('openauth/popup_close.html').render(RequestContext(request, { 'error' : "Please register", 'service':site })))
            return HttpResponse(message)

        #if email and User.objects.filter(email = email).count() != 0 :
        #    tmpl = loader.get_template('openauth/exists.html')
        #    ctx = RequestContext(request, {
        #        'email' : email,
        #    })
        #    return HttpResponse(tmpl.render(ctx))
        #
        # TODO -- 
        #
        user = request.user

        if email :
            from profile.models import UserEmail
            
            try :
                obj = UserEmail.objects.get(user=user, email=email)
                obj.is_confirmed = True
                obj.save()
            except UserEmail.DoesNotExist :
                if not UserEmail.objects.filter(email=email, is_confirmed=True).exists() :
                    obj = UserEmail(user=user, email=email, is_confirmed=True)
                    obj.save()

        oiuser = OpenUser(user=user, openid=identity, source='openid', data=open_user_data)
        oiuser.save()

    if user :
        otoken = None

        if auth_response :
            otoken = auth_response.extensionResponse('http://specs.openid.net/extensions/oauth/1.0', True)

        if email :
            from profile.models import UserEmail
            eu = None
            try :
                eu = UserEmail.objects.get(user=user, email=email)
                if not eu.is_confirmed :
                    eu.is_confirmed = True
                    eu.save()
            except UserEmail.DoesNotExist :
                eu = UserEmail(user=user, email=email, is_confirmed=True)
                eu.save()

        if otoken and len(otoken) != 0 and otoken.has_key('request_token') :
            #
            #  Now upgrade to access token...
            #
            c   = OpenUser.client_for(site)
            tok = c.get_access_token(otoken['request_token'])

            try :
                ot = OAuthStore.objects.get(user=user, source=site)
                ot.token  = tok['oauth_token']
                ot.secret = tok['oauth_token_secret']
                ot.save()
            except OAuthStore.DoesNotExist :
                ot = OAuthStore.objects.create(user=user, source=site, token = tok['oauth_token'], secret = tok['oauth_token_secret'])
        elif token :
            tok = token
            try :
                ot = OAuthStore.objects.get(user=user, source=site)
                ot.token  = tok['oauth_token']
                ot.secret = tok['oauth_token_secret']
                ot.save()
            except OAuthStore.DoesNotExist :
                ot = OAuthStore.objects.create(user=user, source=site, token = tok['oauth_token'], secret = tok['oauth_token_secret'])

        if request.user.is_anonymous() :
            user = authenticate(user=user)
            login(request, user)

        post_login(site, oiuser, didReg)

        if popup : 
            return HttpResponse(loader.get_template('openauth/popup_close.html').render(RequestContext(request, { 'service':site })))
        return HttpResponseRedirect(nexturl)
    elif not message :
        message = "Failure"

    return HttpResponse(message)

def open_logout(request, nexturl = '/') :
    logout(request)
    return HttpResponseRedirect(nexturl)
    
def open_details(request, site=None, nexturl='/') :
    if request.user.is_anonymous() :
        raise Http404("Must be logged in")

    success = False
    errors  = None

    if request.method == 'POST' :
        form = DetailsForm(request.user, request.POST)
        if form.is_valid() :
            user = request.user
            user.username = form.cleaned_data['username']
            user.email    = form.cleaned_data['email']

            if form.cleaned_data['display'] != '' :
                fn, ln = form.cleaned_data['display'].split(' ', 2)
                user.first_name = fn
                user.last_name  = ln
            print "FN = ",user.get_full_name()

            user.save()
            success = True
        else :
            errors = "<ul class='errorlist'>%s</ul>" % ''.join([
                u'<li>%s</li>' % v for v in form.errors.values() 
            ])

    return HttpResponse(json.dumps({'success':success, 'errhtml':errors}), mimetype="application/json")

#
#
#
def loadGoogleAB(user) :
    import gdata.auth
    import gdata.contacts.service
    from friends.models import Contact

    try :
        oauth = OAuthStore.objects.get(user = user, source = 'google')
        token = oauth.token
        secret = oauth.secret
    except OAuthStore.DoesNotExist :
        token = None

    client = gdata.contacts.service.ContactsService()

    iparam = gdata.auth.OAuthInputParams(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                   settings.GOOGLE_OAUTH_KEY,
                                   settings.GOOGLE_OAUTH_SECRET)
                                   #extra_parameters = { 'token' : token })

    client.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                   settings.GOOGLE_OAUTH_KEY,
                                   settings.GOOGLE_OAUTH_SECRET)

    ot = gdata.auth.OAuthToken(token,
                               secret,
                               scopes=[client.GetFeedUri()],
                               oauth_input_params=iparam)

    client.SetOAuthToken(ot)

    otoken = client.FetchOAuthRequestToken()

    feed = client.GetContactsFeed()
    data = []

    for entry in feed.entry :
        for em in entry.email :
            try :
                c = Contact(user=user, name=entry.title.text, email=em.address, source='google')
                c.save()
            except :
                # Hopefully duplicate key
                pass

#
#
#
def post_login(site, openuser, created=False) :
    print "post login for %s created=%r" % ( site, created )

    if site == 'linkedin' :
        client = openuser.client('linkedin')

        data = client.oauth_request('https://api.linkedin.com/v1/people/~:(id,first-name,last-name,picture-url,member-url-resources,public-profile-url)')

        from lxml import etree
        from cStringIO import StringIO

        root = etree.parse(StringIO(data))

        openuser.user.first_name = root.findtext('first-name')
        openuser.user.last_name = root.findtext('last-name')

        openuser.user.save()

        print "FN  = ", root.findtext('first-name')
        print "LN  = ", root.findtext('last-name')
        print "IMG = ", root.findtext('picture-url')
        print "URL = ", root.findtext('public-profile-url')


#
#  The new world order...
#
def signin(request) :
    from .forms import SignInForm

    if request.method == 'POST' :
        sign_in = SignInForm(request.POST)
        if sign_in.is_valid() :
            user = sign_in.get_user()
            user = authenticate(user=user)
            login(request, user)

            return HttpResponseRedirect(request.build_absolute_uri(reverse('point:dashboard')))
    else :
        sign_in = SignInForm()

    tmpl = loader.get_template('openauth/signin.html') 
    return HttpResponse(tmpl.render(RequestContext(request, {
        'sign_in' : sign_in,
    })))

def signup(request) :
    from .forms import SignUpForm

    if request.method == 'POST' :
        sign_up = SignUpForm(request.POST)
        if sign_up.is_valid() :
            user = sign_up.save(request)
            user = authenticate(user=user)
            login(request, user)
            return HttpResponseRedirect(request.build_absolute_uri(reverse('dashboard')))
    else :
        sign_up = SignUpForm()

    tmpl = loader.get_template('openauth/signup.html') 
    return HttpResponse(tmpl.render(RequestContext(request, {
        'sign_up' : sign_up,
    })))

def signup_confirm(request) :
    if request.user.is_anonymous() :
        raise Http404('Not logged in')

    tmpl = loader.get_template('openauth/signup_confirm.html') 
    return HttpResponse(tmpl.render(RequestContext(request, {
        'no_top_links' : True,
        'services'     : settings.OPENAUTH_DATA.keys(),
    })))

def signin_up(request) :
    from .forms import SignInForm, SignUpForm

    sign_in = SignInForm()
    sign_up = SignUpForm()

    tmpl = loader.get_template('openauth/signin_up.html') 
    return HttpResponse(tmpl.render(RequestContext(request, {
        'sign_in' : sign_in,
        'sign_up' : sign_up,
    })))

def connected(request) :
    error = request.GET.get('error', None)
    site  = request.GET.get('site', None)

    async = AsyncResponse(request) 

    if error :
        async.dialog(title="Connect Error", html=error)
    elif request.user.is_anonymous() :
        async.dialog(title='Error', html="<div>must be logged in</div>")
    elif 'next' in request.GET and request.GET['next'] :
        async.redirect(request.GET['next'])
    elif site : 
        async.replace_with('#%s_connect' % site, '<span id="%s_connect">Connected</span>' % site)
        #async.replace('#continue_block', html=" <a class='connect button arrow_white' href='%s'>Done</a>" % reverse('profile:signup'))
        async.replace('#continue_block', html="""<a class='connect button' onclick="javascript:pageTracker._trackEvent('Signup', 'Done');" href='%s'>Done</a>""" % reverse('point:home'))
    
    return async

def open_dialog(request) :
    from .forms import SignInForm, SignUpForm

    async = AsyncResponse(request)
    next  = request.GET.get('next', '/')
    if next[0] != '/' :
        next = '/'

    if request.method == 'POST' :
        sign_in = SignInForm(request.POST)
        if sign_in.is_valid() :
            user = sign_in.get_user()
            user = authenticate(user=user)
            login(request, user)

            return HttpResponseRedirect(request.build_absolute_uri(reverse('point:home')))
    else :
        sign_in = SignInForm()
        sign_up = SignUpForm()

    return async.dialog(title="Login", template='openauth/_dialog.html', modal=True, width=600, options={ 
                            'sign_in' : sign_in, 
                            'sign_up' : sign_up, 
                            'show' : True,
                            'next' : next,
                    }).track('/openauth/signin/dialog')

    return async

def signinup(request) :
    from .forms import SignInUpForm, UserEmail
    from .models import create_user

    if request.method == 'POST' :
        forgot = request.POST.get('forgot', None)
        if forgot :
            email = request.POST.get('email', None)
            if email :
                email = email.strip()
            
            if not UserEmail.objects.filter(email=email).exists() :
                pass
            else :
                for ue in UserEmail.objects.filter(email=email, is_confirmed=True).all() :
                    PasswordRecovery.objects.filter(user=ue.user).delete()
                    r = PasswordRecovery.create(user=ue.user)
                    r.save()

                from django.core.mail import EmailMultiAlternatives

                url = request.build_absolute_uri(reverse('openauth:recover', kwargs={ 'code' : r.rcode }))

                body_text = render_to_string('openauth/_email_recover.txt', RequestContext(request, {
                            'addr' : email,
                            'url'  : url,
                        }))
                body_html = render_to_string('openauth/_email_recover.html', RequestContext(request, {
                            'addr' : email,
                            'url'  : url,
                        }))

                msg = EmailMultiAlternatives('Notewave | Recover Password', body_text, 'help@notewave.com', [email])
                msg.attach_alternative(body_html, 'text/html')
                try :
                    msg.send(fail_silently=True)
                except Exception, e :
                    print e

            return render_to_response('openauth/recovery_sent.html', {
                                                    'email' : email,
                                            }, context_instance=RequestContext(request))

        else :
            form = SignInUpForm(request.POST)
            if form.is_valid() :
                user = form.get_user()
                if not user :
                    if not UserEmail.objects.filter(email=form.cleaned_data['email'], is_confirmed=True).exists() :
                        user = create_user(request, form.cleaned_data['email'], form.cleaned_data['password'])
                    else :
                        form._errors[''] = "Password mismatch"

                if user :
                    user = authenticate(user=user)
                    login(request, user)

                    return HttpResponseRedirect(reverse('point:home'))
    else :
        form = SignInUpForm()

    return render_to_response('openauth/signin.html', {
                                    'sign_in' : form,
                                }, context_instance=RequestContext(request))

def recover(request, code=None) :
    from .forms import RecoveryForm

    try :
        recovery = PasswordRecovery.objects.get(rcode=id)
    except PasswordRecovery.DoesNotExist :
        return render_to_response('openauth/recovery.html', {
                                    'id' : None,
                                }, context_instance=RequestContext(request))

    if request.method == 'POST' :
        form = RecoveryForm(request.POST)
        if form.is_valid() :
            user = recovery.user

            user.set_password(form.cleaned_data['password'])
            user.save()
            recovery.delete()

            user = authenticate(user=user)
            login(request, user)

            # TODO - messages.success(request, 'Your password has been updated')

            return HttpResponseRedirect('/')
    else :
        form = RecoveryForm()

    return render_to_response('openauth/recovery.html', {
                                    'form' : form,
                                    'id'   : recovery.rcode,
                                }, context_instance=RequestContext(request))
