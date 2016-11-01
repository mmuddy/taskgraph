from django.shortcuts import render
from taskgraph.tasktracker.getinterface import get_interface
from django.shortcuts import redirect
from taskgraph.model.model import *
from tulip import *
from pprint import pprint


def analysis_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/analysis.html', context)


def edit_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/edit.html', context)


def graph_view_page(request):
    info = {
        '1': ['Task1', 'Task1 category', 'Task1 performer', 0.66, 'Solved'],
        '2': ['Task2', 'Task2 category', 'Task2 performer', 0.66, 'Solved'],
        '3': ['Task3', 'Task3 category', 'Task3 performer', 0.66, 'Solved'],
        '4': ['Task4', 'Task4 category', 'Task4 performer', 0.66, 'Solved'],
        '5': ['Task5', 'Task5 category', 'Task5 performer', 0.66, 'Solved'],
        '6': ['Task6', 'Task6 category', 'Task6 performer', 0.66, 'Unsolved'],
        '7': ['Task7', 'Task7 category', 'Task7 performer', 0.66, 'Unsolved'],
        '8': ['Task8', 'Task8 category', 'Task8 performer', 0.66, 'Unsolved'],
        '9': ['Task9', 'Task9 category', 'Task9 performer', 0.66, 'Unsolved'],
        '10': ['Task10', 'Task10 category', 'Task10 performer', 0.66, 'Unsolved'],
        '11': ['Task11', 'Task11 category', 'Task11 performer', 0.66, 'Unsolved'],
        '12': ['Task12', 'Task12 category', 'Task12 performer', 0.66, 'Unsolved'],
        '13': ['Task13', 'Task13 category', 'Task13 performer', 0.66, 'Unsolved'],
    }

    graph = {
        '1': ['2', '3', '4', '13'],
        '2': ['5', '6'],
        '3': ['5', '6', '13'],
        '4': ['6'],
        '5': ['7', '13'],
        '6': ['7', '8'],
        '7': ['9', '10'],
        '8': ['10', '11'],
        '9': ['12', '13'],
        '10': ['12'],
        '11': ['12', '13'],
        '12': ['13'],
        '13': [],
    }

    tgraph = tlp.newGraph()

    tulip_graph = {}

    for i in graph:
        node = tgraph.addNode()
        tulip_graph[node] = [i] + info[i]
        info[i] += [node]

    for i in graph:
        for j in graph[i]:
            tgraph.addEdge(info[i][-1], info[j][-1])

    viewSize = tgraph.getSizeProperty("viewSize")
    viewShape = tgraph.getIntegerProperty("viewShape")

    for n in tgraph.getNodes():
        viewSize[n] = tlp.Size(40, 80, 1)
        viewShape[n] = tlp.NodeShape.Square

    tgraph.applyLayoutAlgorithm('Hierarchical Graph', tgraph.getLayoutProperty("viewLayout"))

    min_x = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    max_x = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    min_y = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())
    max_y = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())

    diff_y = max_y - min_y or 1
    diff_x = max_x - min_x or 1

    for node in tgraph.getNodes():
        tulip_graph[node] += (tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] - min_x) / diff_x * 1200, \
                             (tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] - min_y) / diff_y * 500

    all_nodes = [tulip_graph[node] for node in tgraph.getNodes()]
    all_edges = [(i, j) for i in graph for j in graph[i]]

    context = {'is_user_active': True,
               'contains_menu': True,
               'all_edges': all_edges,
               'all_nodes': all_nodes,
               'info': info}
    return render(request, 'taskgraph/graph/view.html', context)


def task_edit_page(request):

    try:
        tracker = Tracker.objects.all().get(type='Dummy')
    except Tracker.DoesNotExist:
        tracker = Tracker(type='Dummy')
        tracker.save()
        tracker.restore_project_list()
        tracker.restore_project_tasks()

    request_task_id = request.GET.get('task');
    if request_task_id is None:
        return render(request, 'taskgraph/alerts.html', {'alerts' : [{
            'css_container_class' : '',
            'css_class' : '',
            'name' : 'Error',
            'message' : 'Incorrect URL'
        }]})

    try:
        task = Task.objects.get(identifier=request_task_id)
    except Task.DoesNotExist:
        return render(request, 'taskgraph/alerts.html', {'alerts': [{
            'css_container_class': '',
            'css_class': '',
            'name': 'Error',
            'message': 'Task not found'
        }]})

    project = Project.objects.get(task=task)

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
        return redirect('taskgraph/graph/task-edit/?task=' + str(task.identifier))

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
                'project' : task.project.name,
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
