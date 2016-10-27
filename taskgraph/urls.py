"""taskgraph URL Configuration"""

from taskgraph.view import base, profile, graph

from django.conf.urls import url


urlpatterns = [

    url(r'^$', base.overview_page, name='overview'),

    url(r'signup/', base.signup_page, name='signup'),

    url(r'graph-edit/', graph.edit_page, name='edit'),
    url(r'projects/', graph.projects_page, name='projects'),
    url(r'view/', graph.graph_view_page, name='view'),
    url(r'analysis/', graph.analysis_page, name='analysis'),

    url(r'trackers/', profile.trackers_page, name='trackers'),
    url(r'trackers-list/', profile.trackers_list_page, name='trackers-list'),
    url(r'trackers-add/', profile.trackers_add_page, name='trackers-add'),
    url(r'trackers-edit/(-?\d+)/', profile.trackers_edit_page, name='trackers-edit'),
    url(r'trackers-delete/(-?\d+)/', profile.trackers_delete, name='trackers-delete'),

]
