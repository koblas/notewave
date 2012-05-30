from django.conf.urls.defaults import *
import os

# Uncomment the next two lines to enable the admin:
urlpatterns = patterns('info.views',
    #(r'^support/dialog$', 'support_dialog'),
    (r'^(?P<page>\w+)', 'dispatch'),
)
