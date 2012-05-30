from django.conf.urls.defaults import *

urlpatterns = patterns('door.views',
    url(r'^cometd', 'cometd'),
    url(r'^join', 'chat.join'),
    #url(r'^recvx', 'chat.recvx'),
    url(r'^recv', 'chat.recvx'),
    url(r'^frog', 'chat.frog'),
    url(r'^send', 'chat.send'),
    url(r'^who', 'chat.who'),
    url(r'^$', 'home', name='home'),
)
