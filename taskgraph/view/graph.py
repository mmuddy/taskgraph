from taskgraph.model.model import Project
from taskgraph.tasktracker.getinterface import get_interface
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
                   'alerts': [alertfactory.warning('No active project!')]}
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
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/task_edit.html', context)
