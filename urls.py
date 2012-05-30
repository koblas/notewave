import os
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from django import template
template.add_to_builtins('snippets.templatetags.partial')
template.add_to_builtins('snippets.templatetags.switch')

urlpatterns = patterns('',
    # Example:
    # (r'^spaces/', include('spaces.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),

    url(r'^(favicon.ico)',  'django.views.static.serve', { 'document_root' : os.path.join(os.path.dirname(__file__), 'static/images') }),
    url(r'^(robots.txt)',  'django.views.static.serve', { 'document_root' : os.path.join(os.path.dirname(__file__), 'static') }),
    (r'^static/(.*)',  'django.views.static.serve', { 'document_root' : os.path.join(os.path.dirname(__file__), 'static/') }),
    #url(r'^', include('door.urls', namespace='doors')),
    url(r'^openauth/', include('openauth.urls', namespace='openauth')),
    url(r'^profile/', include('profile.urls', namespace='profile')),
    url(r'^image/', include('image.urls', namespace='image')),
    url(r'^info/', include('info.urls', namespace='info')),
    url(r'^', include('point.urls', namespace='point')),
)
