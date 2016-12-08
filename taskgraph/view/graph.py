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

    #if len(edge_list) > len(adjacency_matrix) / 2:
    #    tgraph.applyLayoutAlgorithm('Upward Planarization (OGDF)', tgraph.getLayoutProperty("viewLayout"))
    #else:
    #    tgraph.applyLayoutAlgorithm('Random layout', tgraph.getLayoutProperty("viewLayout"))
    tgraph.applyLayoutAlgorithm('Planarization Grid (OGDF)', tgraph.getLayoutProperty("viewLayout"))
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
               'assignees': [i.name for i in project.assignees if i.name != '__NONE'],
               'milestones': [i.name for i in project.milestones if i.name != '__NONE'],
               'states': [i.name for i in project.task_states if i.name != '__NONE'],
               'categories': [i.name for i in project.task_categories if i.name != '__NONE'],
               'relation_types': [i.name for i in project.task_relation_types]}

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

    #if len(edge_list) > len(adjacency_matrix) / 2:
    #    tgraph.applyLayoutAlgorithm('Upward Planarization (OGDF)', tgraph.getLayoutProperty("viewLayout"))
    #else:
    #    tgraph.applyLayoutAlgorithm('Random layout', tgraph.getLayoutProperty("viewLayout"))
    tgraph.applyLayoutAlgorithm('Planarization Grid (OGDF)', tgraph.getLayoutProperty("viewLayout"))
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

    alerts = []
    request_task_id = request.GET.get('task')
    if request_task_id is None:
        context = {
            'is_user_active': True,
            'contains_menu': True,
            'alerts': [alertfactory.error('Incorrect URL')],
            'no_errors': False
        }
        return render(request, 'taskgraph/graph/task_edit.html', context)

    project = Project.objects.filter(is_active=True)
    if project.count() == 0:
        context = {'is_user_active': True,
                   'contains_menu': True,
                   'alerts': [alertfactory.warning('No active project, please choose one on the Project page!')],
                   'no_errors': False}
        return render(request, 'taskgraph/graph/task-edit.html', context)
    assert len(project) == 1
    project = project[0]

    task = filter(lambda t: t.identifier == int(request_task_id), project.tasks)
    if not task:
        context = {
            'is_user_active': True,
            'contains_menu': True,
            'alerts': [alertfactory.error('Task not found')],
            'no_errors': False
        }
        return render(request, 'taskgraph/graph/task_edit.html', context)
    task = task[0]

    if request.method == 'POST':
        if task.assignee.name != '__NONE':
            task.assignee = filter(lambda a: a.name == request.POST.get('Assignee'), project.assignees)[0]
        if task.milestone.name != '__NONE':
            task.milestone = filter(lambda m: m.name == request.POST.get('Milestone'), project.milestones)[0]
        if task.state.name != '__NONE':
            task.state = filter(lambda s: s.name == request.POST.get('State'), project.task_states)[0]
        if task.category.name != '__NONE':
            task.category = filter(lambda c: c.name == request.POST.get('Category'), project.task_categories)[0]
        for field in task.additional_field:
            value = request.POST.get(field.name.replace('_', ' ').capitalize())
            try:
                if field.type == 'CharField':
                    field.char = value
                elif field.type == 'TextField':
                    field.text = value
                elif field.type == 'DateField':
                    field.date = value
                task.save(save_on_tracker=True, i_tracker=get_interface(project.tracker.type))
            except Exception as e:
                alerts.append(alertfactory.error('Incorrect value of field ' + field.name.replace('_', ' ').capitalize()
                                                 + ' (' + field.type + ')'))
                break

        if not alerts:
            try:
                task.save(save_on_tracker=True, i_tracker=get_interface(project.tracker.type))
            except:
                alerts.append(alertfactory.error('Task saving error'))

        if not alerts:
            alerts = [alertfactory.success('Task succesfully updated')]

    meta_fields = []
    if task.assignee.name != '__NONE':
        meta_fields.append({'name': 'Assignee', 'value': task.assignee.name,
                            'list': [assignee.name for assignee in project.assignees if assignee.name != '__NONE']})
    if task.milestone.name != '__NONE':
        meta_fields.append({'name': 'Milestone', 'value': task.milestone.name,
                            'list': [milestone.name for milestone in project.milestones if milestone.name != '__NONE']})
    if task.category.name != '__NONE':
        meta_fields.append({'name': 'Category', 'value': task.category.name,
                            'list': [category.name for category in project.task_categories if category.name != '__NONE']})
    if task.state.name != '__NONE':
        meta_fields.append({'name': 'State', 'value': task.state.name,
                            'list': [state.name for state in project.task_states if state.name != '__NONE']})

    add_fields = []
    for field in task.additional_field:
        name = field.name.replace('_', ' ').capitalize()
        type = field.type
        if type == 'CharField':
            value = field.char
        elif type == 'TextField':
            value = field.text
        elif type == 'DateField':
            value = str(field.date)
        add_fields.append({'name': name, 'type': type, 'value': value})

    to_relations = [{'id': i.from_task.identifier, 'type': i.type.name}
                      for i in filter(lambda r: r.project == project and r.to_task == task, project.tasks_relations)]
    from_relations = [{'id': i.to_task.identifier, 'type': i.type.name}
                    for i in filter(lambda r: r.project == project and r.from_task == task, project.tasks_relations)]

    context = {'is_user_active': True,
                'contains_menu': True,
                'no_error': True,
                'project' : project.name,
                'task_id': task.identifier,
                'meta_fields': meta_fields,
                'add_fields': add_fields,
                'to_relations' : to_relations,
                'from_relations': from_relations,
                'alerts': alerts
    }
    return render(request, 'taskgraph/graph/task_edit.html', context)


def change_graph(request):

    project = Project.objects.filter(is_active=True)
    if project.count() == 0:
        return HttpResponse('Error! No active project')
    assert len(project) == 1
    project = project[0]
    history = json.loads(request.POST['history'])
    changes_count = 0
    changes = len(history)

    for curr in history:
        type = curr['type']
        action = curr['action']
        id = curr['id']

        if type == 'task':

            if action == 'add':
                #todo: add task
                pass
            else:
                id = int(id) if id[0] != '_' else 12345
                task = filter(lambda t: t.identifier == id, project.tasks)
                if not task:
                    return HttpResponse('Error! There is no task with id ' + str(id) + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')
                task = task[0]

                if action == 'changeStatus':
                    try:
                        task.state = filter(lambda s: s.name == curr['status'], project.task_states)[0]
                        changes_count += 1
                    except:
                        return HttpResponse('Error! There is no state ' + curr['status'] + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')
                elif action == 'changeAssignee':
                    try:
                        task.assignee = filter(lambda a: a.name == curr['assignee'], project.assignees)[0]
                        changes_count += 1
                    except:
                        return HttpResponse('Error! There is no assignee ' + curr['assignee'] + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')
                elif action == 'changeCategory':
                    try:
                        task.category = filter(lambda s: s.name == curr['category'], project.task_categories)[0]
                        changes_count += 1
                    except:
                        return HttpResponse('Error! There is no category ' + curr['category'] + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')
                elif action == 'changeMilestone':
                    try:
                        task.state = filter(lambda m: m.name == curr['milestone'], project.milestones)[0]
                        changes_count += 1
                    except:
                        return HttpResponse('Error! There is no milestone ' + curr['milestone'] + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')

                task.save(save_on_tracker=True, i_tracker=get_interface(project.tracker.type))

        elif type == 'relation':

            if action == 'add':
                #todo: add relation
                pass
            elif action == 'delete':
                #todo: delete realtion
                pass
            elif action == 'changeType':
                relation = filter(lambda r: r.identifier == id, project.tasks_relations)
                if (len(relation) == 0):
                    return HttpResponse('Error! There is no relation with id ' + str(id) + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')
                relation = relation[0]
                try:
                    relation.type = filter(lambda t: t.name == curr['param'], project.task_relation_types)[0]
                    changes_count += 1
                except:
                    return HttpResponse('Error! There is no relation type ' + curr['param'] + ' at this project ('
                                        + str(changes_count) + '/' + str(changes) + ' changes applied)')

        #todo: requests to tracker

    return HttpResponse('Graph was successfully updated')
