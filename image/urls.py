from django.conf.urls.defaults import *

urlpatterns = patterns('image.views',
    url(r'^(?P<mod>[^/]+)/(?P<uid>\w+)_(?P<size>\d+x\d+).(?P<fmt>\w+)', 'icon', name="icon"),
)
