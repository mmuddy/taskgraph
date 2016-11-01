from taskgraph.tasktracker.getinterface import get_interface
from taskgraph.model.model import Tracker, Project
from django.shortcuts import render
from django.http import HttpResponse
from json import dumps, loads


def projects_page(request):
    context = {'is_user_active': True,
               'contains_menu': True,
               'tree_json': dumps(_tree_view_json())}

    return render(request, 'taskgraph/graph/projects.html', context)


def post_projects(request):
    if request.method != 'POST':
        raise AssertionError()

    for project in Project.objects.all():
        project.is_active = False
        project.save()

    active = loads(request.body.decode('utf-8'))
    for active_elem in active:
        user_name = active_elem[-4]['name']
        url = active_elem[-3]['name']
        tracker_type = active_elem[-2]['name']
        tracker = Tracker.objects.get(user_name=user_name, url=url, type=tracker_type)
        for project in active_elem[0:-4]:
            model = tracker.project_set.get(name=project['name'])
            model.is_active = True
            model.save()
    return HttpResponse('ok')


def _tree_view_json():
    trackers = []
    visited_tracker = set()
    for type_name in Tracker.Supported:
        last_tracker = {'text': type_name.name, 'selectable': False, 'nodes': []}
        trackers.append(last_tracker)

        for tracker in Tracker.objects.filter(type__exact=type_name.name):
            i_tracker = get_interface(tracker.type)

            tracker.update_projects_if_not_created(i_tracker)

            with i_tracker.connect(tracker):
                current_name = i_tracker.my_name()

            last_url = {'text': tracker.url, 'selectable': False, 'nodes': []}
            last_tracker['nodes'].append(last_url)

            for user in Tracker.objects.filter(type__exact=type_name.name, url=tracker.url):
                if user in visited_tracker:
                    continue
                visited_tracker.add(user)

                last_user = {'text': tracker.user_name, 'selectable': False, 'nodes': []}
                last_url['nodes'].append(last_user)

                p_tree = _project_tree(user, current_name)
                if p_tree:
                    last_user['nodes'] = p_tree

    return trackers


def _project_tree(account, current_name):
    # TODO : check how to deal with sophisticated queries in ORM

    t_json = []

    def handle_project(project, parent_json):
        current_json = _project_json(project, current_name)
        parent_json.append(current_json)
        project_children = account.projectrelation_set.filter(parent=project)

        if project_children.count() != 0:
            current_json['nodes'] = []
            for child in project_children:
                handle_project(child.child, current_json['nodes'])

    top_lvl_projects = []
    for project_model in account.project_set.all():
        if account.projectrelation_set.filter(child=project_model).count() == 0:
            top_lvl_projects.append(project_model)

    for top_project in top_lvl_projects:
        handle_project(top_project, t_json)

    return t_json


def _project_json(project_model, current_name):
    p_json = {'text': project_model.name}

    if project_model.is_member(current_name):
        p_json['icon'] = "glyphicon glyphicon-user"
    else:
        p_json['selectable'] = False

    if project_model.is_active:
        p_json['state'] = {'selected': True}

    return p_json
