"""taskgraph URL Configuration"""

from . import views

from django.conf.urls import url


urlpatterns = [

    url(r'^$', views.project_overview_page, name='overview'),

    url(r'signup/', views.signup_page, name='signup'),

    url(r'edit/', views.edit_page, name='edit'),
    url(r'projects/', views.projects_page, name='projects'),
    url(r'view/', views.graph_view_page, name='view'),
    url(r'analysis/', views.analysis_page, name='analysis'),

    url(r'trackers/', views.trackers_page, name='trackers'),

]
