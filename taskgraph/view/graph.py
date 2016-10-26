from django.shortcuts import render
from taskgraph.tasktracker.getinterface import get_interface
from taskgraph.model.model import Tracker, Project


def analysis_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/analysis.html', context)


def edit_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/edit.html', context)


def projects_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}

    for tracker in Tracker.objects.all():
        tracker.restore_project_list(get_interface(tracker.type))

    Project.objects.all()

    return render(request, 'taskgraph/graph/projects.html', context)


def graph_view_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/view.html', context)
