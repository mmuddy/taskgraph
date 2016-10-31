from django.shortcuts import render
from taskgraph.tasktracker.getinterface import get_interface
from taskgraph.model.model import *


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

    Project.objects.all()

    return render(request, 'taskgraph/graph/projects.html', context)


def graph_view_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/view.html', context)


def task_edit_page(request):

    try:
        tracker = Tracker.objects.all().get(type='Dummy')
    except Tracker.DoesNotExist:
        tracker = Tracker(type='Dummy')
        tracker.save()

    tracker.restore_project_list(get_interface(tracker.type))
    project = tracker.project_set.all()[0]
    project.restore_project_tasks(get_interface(tracker.type))
    task = project.task_set.all()[0]

    add_fields = []
    tags = ('<input value="{}" class="form-control">',
            '<textarea style="margin: 5px; width: 93%" rows="5" class="form-control">{}</textarea>',
            '<input type="date" value="{}" class="form-control"')
    for field in task.taskadditionalfield_set.filter(project = project, task = task):
        add_fields += [[field.name, tags[int(field.type)].format(field.char)]]

    to_relations = [('Task id: ' + str(i.from_task.identifier) + ', relation: ' + i.type.name)
                      for i in project.taskrelation_set.filter(project = project, to_task = task)]
    from_relations = [('Task id: ' + str(i.to_task.identifier) + ', relation: ' + i.type.name)
                      for i in project.taskrelation_set.filter(project = project, from_task = task)]

    context = {'is_user_active': True,
                'contains_menu': True,
                'project' : task.project.name,
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
