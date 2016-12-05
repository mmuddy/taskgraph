from taskgraph.model.model import Project
from taskgraph.model.model import Task
from taskgraph.model.model import TaskRelation
from taskgraph.model.model import *
from taskgraph.tasktracker.getinterface import get_interface
from django.shortcuts import redirect
from taskgraph.model.model import *
from tulip import *
from pprint import pprint
from . import alertfactory, graphview
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
import json



def analysis_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/analysis.html', context)


def edit_page(request):
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

    if len(edge_list) > len(adjacency_matrix) / 2:
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
               'info': info,
               'project_id': project.identifier}

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

    if len(edge_list) > len(adjacency_matrix) / 2:
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
               'info': info,
               'project_id': project.identifier}

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

    alerts = []
    request_task_id = request.GET.get('task');
    request_project_id = request.GET.get('project');
    if request_task_id is None or request_project_id is None:
        context = {
            'is_user_active': True,
            'contains_menu': True,
            'alerts': [alertfactory.error('Incorrect URL')],
            'no_errors': False
        }
        return render(request, 'taskgraph/graph/task_edit.html', context)

    try:
        project = Project.objects.get(identifier=request_project_id)
    except Project.DoesNotExist:
        context = {
            'is_user_active': True,
            'contains_menu': True,
            'alerts': [alertfactory.error('Project not found')],
            'no_errors': False
        }
        return render(request, 'taskgraph/graph/task_edit.html', context)

    try:
        task = Task.objects.get(identifier=request_task_id, project=project)
    except Task.DoesNotExist:
        context = {
            'is_user_active': True,
            'contains_menu': True,
            'alerts': [alertfactory.error('Task not found')],
            'no_errors': False
        }
        return render(request, 'taskgraph/graph/task_edit.html', context)

    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            task.category = filter(lambda c: c.name == category, project.task_categories)[0]
        except:
            alerts.append(alertfactory.error('There is no task category "' + category + '" in this project'))
        try:
            milestone = request.POST.get('milestone')
            task.milestone = filter(lambda m: m.name == milestone, project.milestones)[0]
        except:
            alerts.append(alertfactory.error('There is no milestone "' + milestone + '" in this project'))
        try:
            assignee = request.POST.get('assignee')
            task.assignee = filter(lambda a: a.name == assignee, project.assignees)[0]
        except:
            alerts.append(alertfactory.error('There is no assignee "' + assignee + '" in this project'))
        try:
            state = request.POST.get('state')
            task.state = filter(lambda s: s.name == state, project.task_states)[0]
        except:
            alerts.append(alertfactory.error('There is no state "' + state + '" in this project'))

        for field in task.additional_field:
            try:
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
            except:
                alerts.append(alertfactory.error('Additional field saving error'))

        if len(alerts) == 0:
            try:
                task.save()
            except:
                alerts.append(alertfactory.error('Task saving error'))

        if len(alerts) == 0: alerts = [alertfactory.success('Task succesfully updated')]

    add_fields = []
    tags = ('<input name="{}" value="{}" class="form-control">',
            '<textarea name="{}" style="margin: 5px; width: 93%" rows="5" class="form-control">{}</textarea>',
            '<input name="{}" type="date" value="{}" class="form-control"')
    for field in task.additional_field:
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
                'no_error': True,
                'project_id' : project.identifier,
                'project' : project.name,
                'task_id': task.identifier,
                'assignee' : task.assignee.name,
                'milestone' : task.milestone.name,
                'category' : task.category.name,
                'state' : task.state.name,
                'assignee_list' : [i.name for i in project.assignees],
                'milestone_list': [i.name for i in project.milestones],
                'category_list': [i.name for i in project.task_categories],
                'state_list': [i.name for i in project.task_states],
                'add_fields': add_fields,
                'to_relations' : to_relations,
                'from_relations': from_relations,
                'alerts': alerts
    }
    return render(request, 'taskgraph/graph/task_edit.html', context)


def change_graph(request):

    for curr in json.loads(request.POST['history']):
        #curr - dict with keys 'type', 'action' etc.
        pass
        #todo: requests to tracker

    return HttpResponse('Done')
    '''


    history = json.loads(request.body.decode("utf-8"))
    type = history['type']
    action = history['action']
    project = Project.objects.filter(is_active=True)[0]

    if type == 'relation' :
        from_task = Task.objects.get(project=project, identifier=history['from'])
        to_task = Task.objects.get(project=project, identifier=history['to'])

        if action == 'add':
            relation_type = TaskRelationType.objects.get(project=project, name=history['relation'])
            relation = TaskRelation(project=project, from_task=from_task, to_task=to_task, type=relation_type)
            relation.save(save_on_tracker=True)

        if action == 'delete':
            relation = TaskRelation.objects.get(project=project, from_task=from_task, to_task=to_task)
            relation.delete(delete_on_tracker=True)

    if type == 'task' :

        if action == 'add':
            assignee = Assignee.objects.get(name=history['assignee'])
            milestone = Milestone.objects.get(name=history['milestone'])
            category = TaskCategory.objects.get(name=history['category'])
            state = TaskState.objects.get(name=history['state'])
            task = Task(project=project, assignee=assignee, milestone=milestone, category=category, state=state)
            task.save(save_on_tracker=True)

        if action == 'delete':
            task = TaskRelation.objects.get(project=project, identifier=history['task_id'])
            task.delete(delete_on_tracker=True)

        if action == 'change':
            task.assignee = Assignee.objects.get(name=history['assignee'])
            task.milestone = Milestone.objects.get(name=history['milestone'])
            task.category = TaskCategory.objects.get(name=history['category'])
            task.state = TaskState.objects.get(name=history['state'])
            task.save(save_on_tracker=True)

    return HttpResponse('Done')'''
