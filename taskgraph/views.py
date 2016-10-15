from django.shortcuts import render

from copy import deepcopy
from pprint import pprint


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
    return render(request, 'taskgraph/graph/projects.html', context)


def graph_view_page(request):

    id_list = {
        1: ['Task1', 'Task1 category', 'Task1 performer', 1, 'Solved'],
        2: ['Task2', 'Task2 category', 'Task2 performer', 1, 'Solved'],
        3: ['Task3', 'Task3 category', 'Task3 performer', 1, 'Solved'],
        4: ['Task4', 'Task4 category', 'Task4 performer', 0.66, 'Solved'],
        5: ['Task5', 'Task5 category', 'Task5 performer', 1, 'Unsolved'],
        6: ['Task6', 'Task6 category', 'Task6 performer', 1.66, 'Solved'],
        7: ['Task7', 'Task7 category', 'Task7 performer', 1.33, 'Unsolved'],
        8: ['Task8', 'Task8 category', 'Task8 performer', 1, 'Unsolved'],
        9: ['Task9', 'Task9 category', 'Task9 performer', 0.66, 'Unsolved'],
        10: ['Task10', 'Task10 category', 'Task10 performer', 1, 'Unsolved'],
        11: ['Task11', 'Task11 category', 'Task11 performer', 0.66, 'Unsolved'],
        12: ['Task12', 'Task12 category', 'Task12 performer', 1, 'Unsolved'],
        13: ['Task13', 'Task12 category', 'Task12 performer', 1, 'Unsolved'],
    }

    save_graph = {
        1: [2, 3, 4, 6],
        2: [5, 6, 7, 8, 10, 11],
        3: [5, 6],
        4: [6],
        5: [7, 11],
        6: [7, 8],
        7: [9, 10],
        8: [10, 11],
        9: [12],
        10: [12],
        11: [12],
        12: [13],
        13: []
    }

    save_graph1 = {
        1: [2, 3, 4],
        2: [],
        3: [],
        4: [],
    }

    # TODO: проверить граф на цикличность?
    # TODO: проверить граф на связность?

    graph = deepcopy(save_graph)

    vertices_by_layers = []
    while graph:  # Составляется список вершин для каждого из слоёв

        vertices_of_last_layer = [i for i in graph if graph[i] == []]

        for i in vertices_of_last_layer:
            del graph[i]
            for j in graph:
                graph[j] = [k for k in graph[j] if k != i]

        vertices_by_layers.insert(0, vertices_of_last_layer)

    graph = deepcopy(save_graph)

    # Убирается транзитивность графа
    dependence_graph = {i: ([], []) for i in graph}
    ## Для каждой вершины составляется список вершин, которые необходимо сделать до неё
    for pred_layer, curr_layer in zip(vertices_by_layers, vertices_by_layers[1:]):

        for pred_elem in pred_layer:

            for to_elem in graph[pred_elem]:
                dependence_graph[to_elem] = (dependence_graph[to_elem][0] + [pred_elem],
                                             list(set(dependence_graph[pred_elem][1] +
                                                      [pred_elem] + dependence_graph[to_elem][1])))

    backward_graph = {i: [] for i in graph}  # Все ребра, которые входят в i
    forward_graph = {i: [] for i in graph}  # Все рёбра, которые выходят из i

    ## Для каждого ребра каждой вершины сравнивается, изменится ли список вершин, которые необходимо сделать до неё
    ##      если удалить это ребро. Если не изменится - ребро транзитивное и его можно удалить
    for dependence_to in dependence_graph:

        for dependence_from in dependence_graph[dependence_to][0]:

            dependence_others = [dependence_graph[i][1] + [i] for i in dependence_graph[dependence_to][0] if
                                 i != dependence_from]

            print(dependence_to, dependence_from, dependence_graph[dependence_from][1] + [dependence_from],
                  list(set(sum(dependence_others, []))))

            if not (set(dependence_graph[dependence_from][1] + [dependence_from]) < set(sum(dependence_others, []))):
                backward_graph[dependence_to] += [dependence_from]
                forward_graph[dependence_from] += [dependence_to]
            else:
                print('EDGE', dependence_from, '->', dependence_to, 'DELETED')

    print('DEPENDENCE GRAPH')
    pprint(dependence_graph)
    print('BACKWARD GRAPH')
    pprint(backward_graph)
    print('FORWARD GRAPH')
    pprint(forward_graph)

    forward_dependence = {i: [] for i in graph}  # Все вершины, которые зависят от i
    backward_dependence = {i: [] for i in graph}  # Все вершины, от которых зависит i
    # Заполняются forward_dependence и backward_dependence
    for vertex in dependence_graph:
        for edge in dependence_graph[vertex][1]:

            if vertex not in forward_dependence[edge]: forward_dependence[edge] += [vertex]

            if edge not in backward_dependence[vertex]: backward_dependence[vertex] += [edge]

    print('FORWARD DEPENDENCE')
    pprint(forward_dependence)
    print('BACKWARD DEPENDENCE')
    pprint(backward_dependence)

    graph = deepcopy(forward_graph)

    vertices_by_layers = []
    while graph:  # Составляется новый список вершин для каждого из слоёв

        vertices_of_last_layer = [i for i in graph if graph[i] == []]

        for i in vertices_of_last_layer:
            del graph[i]
            for j in graph:
                graph[j] = [k for k in graph[j] if k != i]

        vertices_by_layers.insert(0, vertices_of_last_layer)

    graph = deepcopy(forward_graph)

    # Ищутся те пары вершин, для которых соединение стрелочками будет через несколько слоёв
    for index, (curr_layer, next_layer) in enumerate(zip(vertices_by_layers, vertices_by_layers[1:])):
        for from_elem in curr_layer:  # Цикл по всем элементам текущего слоя

            if isinstance(from_elem, list):  # Если мы наткнулись на мнимый элемент
                # print(vertices_by_layers, ' ### ', from_layer, ' # ', next_layer, ' # ', from_elem, to_elem)
                from_elem, to_elem = from_elem
                if to_elem not in next_layer:  # Если стрелка ведёт к элементу, которого опять нет в следующем слое
                    vertices_by_layers[index + 1] += [[from_elem, to_elem]]  # Продолжаем мнимый элемент

            else:
                for to_elem in graph[from_elem]:  # Цикл по всем конечным точкам вершины
                    # print(vertices_by_layers, ' ### ', from_layer, ' # ', next_layer, ' # ', from_elem, to_elem)
                    if to_elem not in next_layer:  # Если стрелка ведёт к элементу, которого нет в следующем слое
                        vertices_by_layers[index + 1] += [[from_elem, to_elem]]  # Добавляем мнимый элемент

    print('VERTICES BY LAYERS')
    print(vertices_by_layers)

    #  Определение важных констант

    vertex_height = 40
    vertex_width = 80
    len_after_start_arrow = 5
    len_before_end_arrow = 20
    len_between_vertices_in_layer = 50
    len_between_arrows = 2
    len_css_triangle = 14
    arrow_width = 2
    margin_left_graph = 50

    max_in_layers = max(len(i) for i in vertices_by_layers)

    graph_height = len_between_vertices_in_layer * (max_in_layers + 1)

    #  Просчёт координат вершин и рёбер

    vertex_coords = {i: [0, 0] for i in graph}

    curr_x_coord = margin_left_graph
    curr_imaginary_vertex = -1

    all_edges = []

    for index_layer, (curr_layer, next_layer) in enumerate(
            zip(vertices_by_layers, vertices_by_layers[1:] + vertices_by_layers[0])):

        count_in_layer = len(curr_layer)

        start_height_in_layer = (max_in_layers - count_in_layer) // 2 + 1

        count_of_edges = 0  # Количество ребер в текущем слое, которые будут рендерится как изгибающиеся
        curr_edge = 0

        for index_elem, curr_elem in enumerate(curr_layer):
            if isinstance(curr_elem, list):

                if (start_height_in_layer + index_elem != (max_in_layers - len(next_layer)) // 2 + 1 +
                    next_layer.index(curr_elem if curr_elem in next_layer else curr_elem[1])):
                    count_of_edges += 1
            else:
                for index_next, next_elem in enumerate(forward_graph[curr_elem]):

                    if (start_height_in_layer + index_elem != (max_in_layers - len(next_layer)) // 2 + 1 +
                        next_layer.index(next_elem if next_elem in next_layer else [curr_elem, next_elem])):
                        count_of_edges += 1

        next_layer_x = curr_x_coord + vertex_width + len_after_start_arrow + len_before_end_arrow + count_of_edges * (
            len_between_arrows + arrow_width) - len_between_arrows

        dist_between_layers = next_layer_x - curr_x_coord - vertex_width - len_css_triangle

        for index_elem, curr_elem in enumerate(curr_layer):

            if isinstance(curr_elem, list):  # Если из мнимого элемента
                vertex_coords[curr_imaginary_vertex] = [curr_x_coord,
                                                        len_between_vertices_in_layer * (
                                                        start_height_in_layer + index_elem) - vertex_height // 2]

                id_list[curr_imaginary_vertex] = [str(curr_elem[0]) + '->' + str(curr_elem[1])]

                to_arrow_x = next_layer_x
                to_arrow_y = len_between_vertices_in_layer * (
                (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(
                    curr_elem if curr_elem in next_layer else curr_elem[1]))

                if vertex_coords[curr_imaginary_vertex][
                    1] + vertex_height // 2 == to_arrow_y:  # Если просто прямая стрелка
                    all_edges += [(curr_elem + [1, curr_x_coord + vertex_width, to_arrow_y, dist_between_layers])]

                elif vertex_coords[curr_imaginary_vertex][
                    1] + vertex_height // 2 > to_arrow_y:  # Если изгибающаяся стрелка вверх
                    all_edges += [(curr_elem + [2, curr_x_coord + vertex_width,
                                                vertex_coords[curr_imaginary_vertex][1] + vertex_height // 2,
                                                len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows) + arrow_width,

                                                curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows),
                                                to_arrow_y,
                                                vertex_coords[curr_imaginary_vertex][
                                                    1] + vertex_height // 2 - to_arrow_y,

                                                curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows) + arrow_width,
                                                to_arrow_y,
                                                dist_between_layers - len_after_start_arrow - curr_edge * (
                                                arrow_width + len_between_arrows) - arrow_width])]
                    curr_edge += 1

                else:  # Если изгибающаяся стрелка вниз
                    all_edges += [(curr_elem + [3, curr_x_coord + vertex_width,
                                                vertex_coords[curr_imaginary_vertex][1] + vertex_height // 2,
                                                len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows) + arrow_width,

                                                curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows),
                                                vertex_coords[curr_imaginary_vertex][
                                                    1] + vertex_height // 2 + arrow_width,
                                                to_arrow_y - vertex_coords[curr_imaginary_vertex][
                                                    1] - vertex_height // 2,

                                                curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                arrow_width + len_between_arrows) + arrow_width,
                                                to_arrow_y,
                                                dist_between_layers - len_after_start_arrow - curr_edge * (
                                                arrow_width + len_between_arrows) - arrow_width])]
                    curr_edge += 1

                curr_imaginary_vertex -= 1


            else:
                vertex_coords[curr_elem][0] = curr_x_coord
                vertex_coords[curr_elem][1] = len_between_vertices_in_layer * (
                start_height_in_layer + index_elem) - vertex_height // 2

                for to_vertex in forward_graph[curr_elem]:

                    to_arrow_x = next_layer_x
                    to_arrow_y = len_between_vertices_in_layer * (
                    (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(
                        to_vertex if to_vertex in next_layer else [curr_elem, to_vertex]))

                    if vertex_coords[curr_elem][1] + vertex_height // 2 == to_arrow_y:  # Если просто прямая стрелка
                        all_edges += [([curr_elem, to_vertex] + [1, curr_x_coord + vertex_width, to_arrow_y,
                                                                 dist_between_layers])]

                    elif vertex_coords[curr_elem][
                        1] + vertex_height // 2 > to_arrow_y:  # Если изгибающаяся стрелка вверх
                        all_edges += [([curr_elem, to_vertex] + [2, curr_x_coord + vertex_width,
                                                                 vertex_coords[curr_elem][1] + vertex_height // 2,
                                                                 len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows) + arrow_width,

                                                                 curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows),
                                                                 to_arrow_y,
                                                                 vertex_coords[curr_elem][
                                                                     1] + vertex_height // 2 - to_arrow_y,

                                                                 curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows) + arrow_width,
                                                                 to_arrow_y,
                                                                 dist_between_layers - len_after_start_arrow - curr_edge * (
                                                                 arrow_width + len_between_arrows) - arrow_width])]
                        curr_edge += 1

                    else:  # Если изгибающаяся стрелка вниз
                        all_edges += [([curr_elem, to_vertex] + [3, curr_x_coord + vertex_width,
                                                                 vertex_coords[curr_elem][1] + vertex_height // 2,
                                                                 len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows) + arrow_width,

                                                                 curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows),
                                                                 vertex_coords[curr_elem][
                                                                     1] + vertex_height // 2 + arrow_width,
                                                                 to_arrow_y - vertex_coords[curr_elem][
                                                                     1] - vertex_height // 2,

                                                                 curr_x_coord + vertex_width + len_after_start_arrow + curr_edge * (
                                                                 arrow_width + len_between_arrows) + arrow_width,
                                                                 to_arrow_y,
                                                                 dist_between_layers - len_after_start_arrow - curr_edge * (
                                                                 arrow_width + len_between_arrows) - arrow_width])]
                        curr_edge += 1

        curr_x_coord = next_layer_x

    pprint(vertex_coords)
    pprint(all_edges)

    vertex_coords = [[vertex_coords[i][0],vertex_coords[i][1]]+[i]+id_list[i] for i in vertex_coords]

    for edge in all_edges:  # edge fix for bootstrap
        edge[3] -= 6
        edge[5] += 6

    for vertex in vertex_coords:  # vertex fix for bootstrap
        if vertex[2] > 0:
            vertex[1] += 3

    context = {
        'is_user_active': True,
        'contains_menu': True,
        'vertex_coords': vertex_coords,
        'id_list': id_list,
        'all_edges': all_edges
    }

    return render(request, 'taskgraph/graph/view.html', context)


def trackers_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers.html', context)


def trackers_list_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers_list.html', context)


def trackers_add_page(request):
    context = {'is_user_active': True,
               'contains_menu': True}
    return render(request, 'taskgraph/profile/trackers_add.html', context)


def profile_page(request):
    return trackers_page(request)


def project_overview_page(request):
    context = {'is_user_active': False,
               'contains_menu': False}
    return render(request, 'taskgraph/overview.html', context)


def signup_page(request):
    context = {'is_user_active': False,
               'contains_menu': False}
    return render(request, 'taskgraph/signup.html', context)