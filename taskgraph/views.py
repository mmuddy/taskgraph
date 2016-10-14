from django.shortcuts import render

from copy import deepcopy


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
    return render(request, 'taskgraph/graph/projects.html', context)


def graph_view_page(request):

    ids = {
        1: 'Task1',
        2: 'Task2',
        3: 'Task3',
        4: 'Task4',
        5: 'Task5',
        6: 'Task6',
        7: 'Task7',
        8: 'Task8',
        9: 'Task9',
        10: 'Task10',
        11: 'Task11',
        12: 'Task12'
    }

    graph = {
        1: [2, 3, 4],
        2: [5, 6],
        3: [5, 6],
        4: [6],
        5: [7],
        6: [7, 8],
        7: [9, 10],
        8: [10, 11],
        9: [12],
        10: [12],
        11: [12],
        12: []
    }

    save_graph = deepcopy(graph)


    layers = []
    while 1:
        empty = []
        for i in graph:
            if graph[i] == []:
                empty += [i]
                del graph[i]
                for j in graph:
                    graph[j] = [k for k in graph[j] if j != i]




    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/view.html', context)


def trackers_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers.html', context)


def trackers_list_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers_list.html', context)


def trackers_add_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers_add.html', context)


def profile_page(request):
    return trackers_page(request)


def project_overview_page(request):
    context = {'is_user_active': False,
               'contains_menu': False}
    return render(request, 'taskgraph/overview.html', context)


def signup_page(request):
    context = {'is_user_active': False,
               'contains_menu': False}
    return render(request, 'taskgraph/signup.html', context)