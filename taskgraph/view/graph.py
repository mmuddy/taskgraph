from django.shortcuts import render
from tulip import *
from math import radians, sqrt, pow
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

    view_size = tgraph.getSizeProperty("viewSize")
    view_shape = tgraph.getIntegerProperty("viewShape")

    vertex_block_width = 40
    vertex_block_height = 80

    for n in tgraph.getNodes():
        view_size[n] = tlp.Size(vertex_block_width, vertex_block_height, 1)
        view_shape[n] = tlp.NodeShape.Square

    tgraph.applyLayoutAlgorithm('Upward Planarization (OGDF)', tgraph.getLayoutProperty("viewLayout"))

    """min_x = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    max_x = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] for node in tgraph.getNodes())
    min_y = min(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())
    max_y = max(tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] for node in tgraph.getNodes())

    diff_y = max_y - min_y or 1
    diff_x = max_x - min_x or 1"""

    edge_lengths = []
    for edge in tgraph.getEdges():
        node_from = tgraph.source(edge)
        node_to = tgraph.target(edge)
        node_from_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_from)
        node_to_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_to)
        edge_lengths.append(sqrt(pow(node_from_value[0] - node_to_value[0], 2) +
                                 pow(node_from_value[1] - node_to_value[1], 2)))

    edge_median = median(edge_lengths)
    ideal_edge = vertex_block_height * 3
    proportion = ideal_edge / edge_median

    for node in tgraph.getNodes():
        tulip_graph[node] += tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] * proportion, \
                             tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] * proportion

    all_nodes = [tulip_graph[node] for node in tgraph.getNodes()]
    all_edges = [(i, j) for i in graph for j in graph[i]]

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
