from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('openauth.views',
    #
    #  Used by Facebook
    #
    (r'xd_receiver.html', direct_to_template, { 'template' : 'openauth/xd_receiver.html' }),

    #
    #  OpenID centralization.
    #
    url(r'xrds', 'xrds', name='xrds'),
    url(r'r/(?P<site>.+)', 'open_prompt', name='prompt'),
    url(r'rp/(?P<site>.+)', 'open_prompt', { 'popup' : True }, name='pop_prompt'),
    url(r'cb/(?P<site>.*)', 'open_callback', name='callback'),
    url(r'cp/(?P<site>.*)', 'open_callback', { 'popup' : True }, name='pop_callback'),

    url(r'details', 'open_details', name='details'),
    url(r'logout', 'open_logout', name='logout'),
    url(r'login-dialog', 'open_dialog', name='dialog'),

    #url(r'signin_up', 'signin_up', name='signinup'),
    url(r'connected', 'connected', name='connected'),
    url(r'pw/(?P<code>[a-zA-Z0-9-]+)', 'recover', name='recover'),
    url(r'signin$', 'signin', name='signin'),
    url(r'signup$', 'signup', name='signup'),
    url(r'signinup$', 'signinup', name='signinup'),
    url(r'signup/confirm$', 'signup_confirm', name='signup_confirm'),
)
