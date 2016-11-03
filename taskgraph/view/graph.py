from taskgraph.model.model import Project, Task, TaskRelation
from taskgraph.tasktracker.getinterface import get_interface
from . import alertfactory, graphview
from django.shortcuts import render

from tulip import *

from math import sqrt, pow
from statistics import median


def analysis_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/analysis.html', context)


def edit_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/edit.html', context)


def graph_view_page(request):
    print(tlp.getLayoutAlgorithmPluginsList())

    project = Project.objects.filter(is_active=True)
    if project.count() == 0:
        context = {'is_user_active': True,
                   'contains_menu': True,
                   'alerts': [alertfactory.warning('No active graph!')]}
        return render(request, 'taskgraph/graph/view.html', context)

    assert len(project) == 1

    project = project[0]
    project.tracker.restore_project_tasks(i_tracker=get_interface(project.tracker.type))
    info, edge_list = graphview.prepare_graph(project)

    tgraph = tlp.newGraph()

    tulip_graph = {}

    for i in info.keys():
        node = tgraph.addNode()
        tulip_graph[node] = info[i]
        info[i] += [node]

    for i in edge_list:
        for j in edge_list[i]:
            tgraph.addEdge(info[i][-1], info[j][-1])

    view_size = tgraph.getSizeProperty("viewSize")
    view_shape = tgraph.getIntegerProperty("viewShape")

    vertex_block_width = 40
    vertex_block_height = 80

    for n in tgraph.getNodes():
        view_size[n] = tlp.Size(vertex_block_width, vertex_block_height, 1)
        view_shape[n] = tlp.NodeShape.Square

    if edge_list:
        tgraph.applyLayoutAlgorithm('Upward Planarization (OGDF)', tgraph.getLayoutProperty("viewLayout"))
    else:
        tgraph.applyLayoutAlgorithm('Random layout', tgraph.getLayoutProperty("viewLayout"))

    """min_x = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    max_x = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    min_y = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())
    max_y = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())

    diff_y = max_y - min_y or 1
    diff_x = max_x - min_x or 1"""

    node_dists = []
    node_list = [node for node in tgraph.getNodes()]

    for node_i in node_list:
        for node_j in node_list[1:int(len(node_list)/2)]:
            node_i_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_i)
            node_j_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_j)
            dist = sqrt(pow(node_i_value[0] - node_j_value[0], 2) +
                                   pow(node_i_value[1] - node_j_value[1], 2))
            if dist:
                node_dists.append(dist)

    ideal_dist = vertex_block_height * 3
    min_dist = min(node_dists)
    proportion = ideal_dist / min_dist

    for node in tgraph.getNodes():
        tulip_graph[node] += tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] * proportion, \
                             tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] * proportion

    all_nodes = [tulip_graph[node] for node in tgraph.getNodes()]
    all_edges = [(i, j) for i in edge_list for j in edge_list[i]]

    context = {'is_user_active': True,
               'contains_menu': True,
               'all_edges': all_edges,
               'all_nodes': all_nodes,
               'info': info}

    return render(request, 'taskgraph/graph/view.html', context)


def task_edit_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/graph/task_edit.html', context)
