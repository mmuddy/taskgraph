from taskgraph.model.model import Project
from taskgraph.tasktracker.getinterface import get_interface
from django.shortcuts import redirect
from taskgraph.model.model import *
from tulip import *
from pprint import pprint
from . import alertfactory, graphview
from django.shortcuts import render



def analysis_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/analysis.html', context)


def edit_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/edit.html', context)


def graph_view_page(request):
    project = Project.objects.filter(is_active=True)

    if project.count() == 0:
        context = {'is_user_active': True,
                   'contains_menu': True,
                   'alerts': [alertfactory.warning('No active project, please choose one on the Project page!')]}
        return render(request, 'taskgraph/graph/view.html', context)

    assert len(project) == 1

    project = project[0]
    i_tracker = get_interface(project.tracker.type)
    project.tracker.restore_project_tasks(i_tracker=i_tracker)
    info, edge_list, adjacency_matrix = graphview.prepare_graph(project, i_tracker)

    vertex_block_width = 40
    tgraph, node_ind = graphview.prepare_tultip(info, edge_list,
                                                vertex_block_width=vertex_block_width,
                                                vertex_block_height=80)

    if edge_list:
        tgraph.applyLayoutAlgorithm('Upward Planarization (OGDF)', tgraph.getLayoutProperty("viewLayout"))
    else:
        tgraph.applyLayoutAlgorithm('Random layout', tgraph.getLayoutProperty("viewLayout"))

    scale_ind = 3
    coords = graphview.normalize_graph_coords(tgraph, vertex_block_width, node_ind, scale_ind)
    all_nodes = [info[node_ind[node]] for node in tgraph.getNodes()]
    all_edges = [(i, j, adjacency_matrix[int(i)][int(j)][0], adjacency_matrix[int(i)][int(j)][1])
                 for i in edge_list for j in edge_list[i]]

    context = {'is_user_active': True,
               'contains_menu': True,
               'all_edges': all_edges,
               'all_nodes': all_nodes,
               'coords': coords,
               'info': info}

    return render(request, 'taskgraph/graph/view.html', context)


def task_edit_page(request):

    try:
        tracker = Tracker.objects.get(type='Dummy')
    except Tracker.DoesNotExist:
        tracker = Tracker(type='Dummy')
        tracker.save()
        tracker.restore_project_list(get_interface(tracker.type))
        for project in tracker.project_set.all() :
            project.restore_project_tasks(get_interface(tracker.type))

    request_task_id = request.GET.get('task');
    request_project_id = request.GET.get('project');
    if request_task_id is None or request_project_id is None:
        return render(request, 'taskgraph/alerts.html', {'alerts' : [{
            'css_container_class' : '',
            'css_class' : '',
            'name' : 'Error',
            'message' : 'Incorrect URL'
        }]})

    try:
        project = Project.objects.get(identifier=request_project_id)
    except Project.DoesNotExist:
        return render(request, 'taskgraph/alerts.html', {'alerts': [{
            'css_container_class': '',
            'css_class': '',
            'name': 'Error',
            'message': 'Project not found'
        }]})

    try:
        task = Task.objects.get(identifier=request_task_id, project=project)
    except Task.DoesNotExist:
        return render(request, 'taskgraph/alerts.html', {'alerts': [{
            'css_container_class': '',
            'css_class': '',
            'name': 'Error',
            'message': 'Task not found'
        }]})

    if request.method == 'POST':
        task.category = project.taskcategory_set.get(name=request.POST.get('category'))
        task.milestone = project.milestone_set.get(name=request.POST.get('milestone'))
        task.assignee = project.assignee_set.get(name=request.POST.get('assignee'))
        task.state = project.taskstate_set.get(name=request.POST.get('state'))
        for field in TaskAdditionalField.objects.filter(task=task):
            if int(field.type) == 0 :
                field.type = 'CharField'
                field.char = request.POST.get(field.name)
            if int(field.type) == 1 :
                field.type = 'TextField'
                field.text = request.POST.get(field.name)
            if int(field.type == 2) :
                field.type = 'DateField'
                field.date = request.POST.get(field.name)
            field.save()
        task.save()
        response = redirect('task-edit')
        response['Location'] += '?task=' + str(task.identifier) + "&project=" + str(project.identifier)
        return response

    add_fields = []
    tags = ('<input name="{}" value="{}" class="form-control">',
            '<textarea name="{}" style="margin: 5px; width: 93%" rows="5" class="form-control">{}</textarea>',
            '<input name="{}" type="date" value="{}" class="form-control"')
    for field in TaskAdditionalField.objects.filter(task=task):
        if int(field.type) == 0:
            add_fields += [{'name': field.name, 'tags': tags[int(field.type)].format(field.name, field.char)}]
        if int(field.type) == 1:
            add_fields += [{'name': field.name, 'tags': tags[int(field.type)].format(field.name, field.text)}]
        if int(field.type) == 2:
            add_fields += [{'name': field.name, 'tags': tags[int(field.type)].format(field.name, field.date)}]

    to_relations = [{'id': i.from_task.identifier, 'type': i.type.name}
                      for i in project.taskrelation_set.filter(project = project, to_task = task)]
    from_relations = [{'id': i.to_task.identifier, 'type': i.type.name}
                      for i in project.taskrelation_set.filter(project = project, from_task = task)]

    context = {'is_user_active': True,
                'contains_menu': True,
                'project_id' : project.identifier,
                'project' : project.name,
                'task_id': task.identifier,
                'assignee' : task.assignee.name,
                'milestone' : task.milestone.name,
                'category' : task.category.name,
                'state' : task.state.name,
                'assignee_list' : [i.name for i in project.assignee_set.all()],
                'milestone_list': [i.name for i in project.milestone_set.all()],
                'category_list': [i.name for i in project.taskcategory_set.all()],
                'state_list': [i.name for i in project.taskstate_set.all()],
                'add_fields': add_fields,
                'to_relations' : to_relations,
                'from_relations': from_relations,
    }
    return render(request, 'taskgraph/graph/task_edit.html', context)
