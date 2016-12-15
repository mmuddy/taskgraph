from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^taskgraph/', include('taskgraph.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^.*', include('taskgraph.urls'))
)
