from django.conf.urls.defaults import *

urlpatterns = patterns('profile.views',
    #url(r'^$', 'show', { 'username' : None }, name="profile_home"),
    url(r'^edit/about$', 'settings_about', name="settings"),
    url(r'^edit/photo$', 'settings_photo', name="settings_photo"),
    url(r'^edit/email$', 'settings_email', name="settings_email"),
    url(r'^edit/notify$', 'settings_notify', name="settings_notification"),
    url(r'^edit/password$', 'settings_password', name="settings_password"),
    url(r'^signup$', 'signup_profile', name="signup"),
    url(r'^c/em/(?P<userid>\w+)/(?P<key>\w+)$', 'confirm_email', name="confirm_email"),
    url(r'^connect$', 'connect', name="connected"),
    url(r'^edit/networks$', 'settings_networks', name="settings_networks"),
    url(r'^action/follow/(?P<userid>\w+)$', 'action_follow', name="action_follow"),
    url(r'^action/message_read/(?P<id>\w+)$', 'message_read', name="message_read"),

    url(r'^(?P<username>\w+)?$', 'show', name="profile"),
    url(r'^(?P<userid>\d+)/(?P<display>.+)?$', 'show', name="profile"),
)
