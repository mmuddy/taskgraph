"""taskgraph URL Configuration"""

from . import views

from django.conf.urls import url


def menu_item_url(menu_item):
    return url(r'^{}/$'.format(menu_item.url), menu_item.view, name=menu_item.url_alias)

urlpatterns = [

    url(r'^$', views.OverviewPage.view, name='taskgraph'),

] + [menu_item_url(menu_item) for menu_item in views.get_menu_items()]
