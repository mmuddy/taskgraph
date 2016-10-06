"""taskgraphproject URL Configuration"""

from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^taskgraph/', include('taskgraph.urls')),
]
