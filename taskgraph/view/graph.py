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
    project = list(Project.objects.all())[0]
    project.restore_project_tasks(get_interface(tracker.type))
    task = list(Task.objects.all())[0]

    add_fields = []
    for field in TaskAdditionalField.objects.filter(project = project, task = task):
        if int(field.type) == 0 :
            add_fields += [[field.name, '<input value="{}" class="form-control">'.format(field.char)]]
        if int(field.type) == 1 :
            add_fields += [[field.name,
                '<textarea style="margin: 5px; width: 93%" rows="5" class="form-control">{}</textarea>'.format(field.text)]]
        if int(field.type) == 2 :
            add_fields += [[field.name, '<input type="date" value="{}" class="form-control"'.format(field.date)]]

    to_relations = [('Task id: ' + str(r.from_task.identifier) + ', relation: ' + r.type.name)
                      for r in TaskRelation.objects.filter(project = project, to_task = task)]
    from_relations = [('Task id: ' + str(r.to_task.identifier) + ', relation: ' + r.type.name)
                      for r in TaskRelation.objects.filter(project = project, from_task = task)]

    context = {'is_user_active': True,
                'contains_menu': True,
                'project' : task.project.name,
                'assignee' : task.assignee.name,
                'milestone' : task.milestone.name,
                'category' : task.category.name,
                'state' : task.state.name,
                'assignee_list' : [a.name for a in Assignee.objects.filter(project = project)],
                'milestone_list': [m.name for m in Milestone.objects.filter(project = project)],
                'category_list': [c.name for c in TaskCategory.objects.filter(project = project)],
                'state_list': [a.name for a in TaskState.objects.filter(project = project)],
                'add_fields': add_fields,
                'to_relations' : to_relations,
                'from_relations': from_relations
    }
    return render(request, 'taskgraph/graph/task_edit.html', context)
