from django.shortcuts import render
from django.http.response import HttpResponse
from django.views import generic

# from . import models


# class DetailView(generic.DetailView):
#    model = models.TrackerConnectionInf

def get_menu_items():
    return AboutPage, OverviewPage


class AboutPage:

    name = 'About'
    url = name.lower()
    url_alias = url

    @staticmethod
    def view(request):
        context = {'menu_items': get_menu_items(),
                   'active_menu_item': AboutPage,
                   'breaks': range(7)}
        return render(request, 'taskgraph/about.html', context)


class OverviewPage:

    name = 'Overview'
    url = name.lower()
    url_alias = url

    @staticmethod
    def view(request):
        context = {'menu_items': get_menu_items(),
                   'active_menu_item': OverviewPage,
                   'breaks': range(7)}
        return render(request, 'taskgraph/overview.html', context)
