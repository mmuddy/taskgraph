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
        14: ['Task14', 'Task12 category', 'Task12 performer', 1, 'Unsolved'],
        15: ['Task15', 'Task12 category', 'Task12 performer', 1, 'Unsolved'],
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
        13: [],
        14: [13],
        15: [14],
    }

    save_graph1 = {
        1: [2, 3, 4],
        2: [],
        3: [],
        4: [],
    }

    ## TODO: проверить граф на цикличность?
    # TODO: проверить граф на связность?

    graph = deepcopy(save_graph)

    vertices_by_layers = []
    while graph:  # Составляется список вершин для каждого из слоёв

        vertices_of_last_layer = [i for i in graph if graph[i] == [] ]

        for i in vertices_of_last_layer:
            del graph[i]
            for j in graph:
                graph[j] = [k for k in graph[j] if k != i]

        vertices_by_layers.insert(0, vertices_of_last_layer)

    graph = deepcopy(save_graph)



    # Убирается транзитивность графа
    dependence_graph = {i: ([],[]) for i in graph}
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

            dependence_others = [dependence_graph[i][1]+[i] for i in dependence_graph[dependence_to][0] if i != dependence_from]

            print(dependence_to, dependence_from, dependence_graph[dependence_from][1]+[dependence_from], list(set(sum(dependence_others,[]))))

            if not(set(dependence_graph[dependence_from][1] + [dependence_from]) < set(sum(dependence_others,[]))):
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

        vertices_of_last_layer = [i for i in graph if graph[i] == [] ]

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
                #print(vertices_by_layers, ' ### ', from_layer, ' # ', next_layer, ' # ', from_elem, to_elem)
                from_elem, to_elem = from_elem
                if to_elem not in next_layer:  # Если стрелка ведёт к элементу, которого опять нет в следующем слое
                    vertices_by_layers[index + 1] += [[from_elem, to_elem]]  # Продолжаем мнимый элемент

            else:
                for to_elem in graph[from_elem]:  # Цикл по всем конечным точкам вершины
                    #print(vertices_by_layers, ' ### ', from_layer, ' # ', next_layer, ' # ', from_elem, to_elem)
                    if to_elem not in next_layer:  # Если стрелка ведёт к элементу, которого нет в следующем слое
                        vertices_by_layers[index + 1] += [[from_elem, to_elem]]  # Добавляем мнимый элемент


    print('VERTICES BY LAYERS')
    print(vertices_by_layers)



    #  Определение важных констант

    vertex_height = 40
    vertex_width  = 80
    len_after_start_arrow = 20
    len_before_end_arrow = 20
    len_between_vertices_in_layer = 100
    len_between_arrows = 2
    len_css_triangle = 14
    arrow_width = 2
    margin_left_graph = 50
    distance_between_slots = 10

    max_in_layers = max(len(i) for i in vertices_by_layers)

    graph_height = len_between_vertices_in_layer * (max_in_layers + 1)





    #  Расставление разных слотов выхода и прихода рёбер в вершины
    edges_slots = {}
    max_slots = max(len(i) for i in [j for j in forward_graph.values()] + [j for j in backward_graph.values()])
    range_slots = [-i for i in range(1,max_slots // 2 + 1)] + [0] + [i for i in range(1,max_slots // 2 + 1)]
    count_of_slots = len(range_slots)

    edges_available_slots_forward  = {elem: [-i for i in range(1,max_slots // 2 + 1)] + [0] + [i for i in range(1,max_slots // 2 + 1)] for elem in graph}
    edges_available_slots_backward = {elem: [-i for i in range(1,max_slots // 2 + 1)] + [0] + [i for i in range(1,max_slots // 2 + 1)] for elem in graph}

    for curr_layer, next_layer in zip(vertices_by_layers, vertices_by_layers[1:]):
        for curr_elem in curr_layer:

            ## Сначала забиваем все прямые связи в нулевые слоты

            if isinstance(curr_elem, list) and curr_elem not in next_layer:  # Если мнимый элемент соединяется с нормальным

                index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(curr_elem[1])
                index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                if index_to == index_from:

                    # !!! Стрелка в другом конце ещё может быть не определена, если не начинает прямо
                    if (curr_elem[0], curr_elem[1]) not in edges_slots:
                        edges_slots[curr_elem[0], curr_elem[1]] = [0]

                    edges_slots[curr_elem[0], curr_elem[1]] += [0]
                    curr_slot = edges_available_slots_backward[curr_elem[1]]
                    del curr_slot[curr_slot.index(0)]


            elif isinstance(curr_elem, int):

                for to_vertex in forward_graph[curr_elem]:

                    if to_vertex not in next_layer:  # Если нормальный элемент соединяется с мнимым

                        index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index([curr_elem, to_vertex])
                        index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                        if index_to == index_from:

                            edges_slots[curr_elem, to_vertex] = [0]
                            curr_slot = edges_available_slots_forward[curr_elem]
                            del curr_slot[curr_slot.index(0)]

                    else:  # Если нормальный элемент соединяется с нормальным

                        index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(to_vertex)
                        index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                        if index_to == index_from:

                            edges_slots[curr_elem, to_vertex] = [0, 0]
                            curr_slot = edges_available_slots_forward[curr_elem]
                            del curr_slot[curr_slot.index(0)]
                            to_vertex_slot = edges_available_slots_backward[to_vertex]
                            del to_vertex_slot[to_vertex_slot.index(0)]

        for curr_elem in curr_layer:

            ## Затем расставляем оставшиеся

            if isinstance(curr_elem, list) and curr_elem not in next_layer:  # Если мнимый элемент соединяется с нормальным

                index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(curr_elem[1])
                index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                if index_to < index_from:  # Стрелка поедет вверх
                    # !!! Стрелка точно определена в edges_slots и имеет длину 1

                    curr_slot = edges_available_slots_backward[curr_elem[1]]

                    # Выбирается ближайший к нулевому слоту положительный, иначе ближайший к нулевому слоту отрицательный
                    slot_number = curr_slot[-1] if all(i <= 0 for i in curr_slot) else [i for i in curr_slot if i > 0][0]

                    edges_slots[curr_elem[0], curr_elem[1]] += [slot_number]
                    del curr_slot[curr_slot.index(slot_number)]

                elif index_to > index_from:  # Стрелка идёт вниз
                    # !!! Стрелка точно определена в edges_slots и имеет длину 1

                    curr_slot = edges_available_slots_backward[curr_elem[1]]

                    # Выбирается ближайший к нулевому слоту отрицательный, иначе ближайший к нулевому слоту положительный
                    slot_number = curr_slot[0] if all(i >= 0 for i in curr_slot) else [i for i in curr_slot if i < 0][-1]

                    edges_slots[curr_elem[0], curr_elem[1]] += [slot_number]
                    del curr_slot[curr_slot.index(slot_number)]


            elif isinstance(curr_elem, int):

                for to_vertex in forward_graph[curr_elem]:

                    if to_vertex not in next_layer:  # Если нормальный элемент соединяется с мнимым

                        index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index([curr_elem, to_vertex])
                        index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                        if index_to < index_from:  # Стрелка поедет вверх
                            # !!! Если элемент определён, то имеет длину 2, в случае если другой конец имеет прямую стрелку, иначе не определён

                            curr_slot = edges_available_slots_forward[curr_elem]

                            if (max_in_layers - len(next_layer)) // 2 + len(next_layer) >= index_from >= (max_in_layers - len(next_layer)) // 2 + 1:  # Если справа есть вершина

                                right_vertex = next_layer[index_from - (max_in_layers - len(next_layer)) // 2 - 1]

                                for candidate_slot in curr_slot:

                                    if candidate_slot in edges_available_slots_backward[right_vertex] if isinstance(right_vertex, int) else candidate_slot != 0 or (
                                            index_from < (max_in_layers-len(curr_layer))//2+1+curr_layer.index(right_vertex if right_vertex in curr_layer else right_vertex[0])):

                                        print('###', curr_layer, curr_elem, to_vertex, curr_slot, candidate_slot, right_vertex, index_to, index_from)
                                        slot_number = candidate_slot
                                        break

                                else:
                                    1
                                    # TODO: обработать очень редкую ситуацию, когда нельзя выйти ни из какого слота - всё приведёт к наложению стрелок
                                    # Здесь HOTFIX, чтобы хотя бы не падало
                                    slot_number = range_slots[-1] + 1
                                    if (curr_elem, to_vertex) in edges_slots:
                                        edges_slots[curr_elem, to_vertex][0] = slot_number
                                    else:
                                        edges_slots[curr_elem, to_vertex] = [slot_number]
                                    continue

                            else: slot_number = curr_slot[0]

                            if (curr_elem, to_vertex) in edges_slots:
                                edges_slots[curr_elem, to_vertex][0] = slot_number
                            else:
                                edges_slots[curr_elem, to_vertex] = [slot_number]

                            del curr_slot[curr_slot.index(slot_number)]

                        elif index_to > index_from:  # Стрелка поедет вниз
                            # !!! Если элемент определён, то имеет длину 2, в случае если другой конец имеет прямую стрелку, иначе не определён

                            curr_slot = edges_available_slots_forward[curr_elem]

                            if (max_in_layers - len(next_layer)) // 2 + len(next_layer) >= index_from >= (max_in_layers - len(next_layer)) // 2 + 1:  # Если справа есть вершина

                                right_vertex = next_layer[index_from - (max_in_layers - len(next_layer)) // 2 - 1]

                                for candidate_slot in [i for i in curr_slot if i > 0] or curr_slot[::-1]:

                                    if candidate_slot in edges_available_slots_backward[right_vertex] if isinstance(right_vertex, int) else candidate_slot != 0 or (index_from < (
                                                        max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(right_vertex if right_vertex in curr_layer else right_vertex[0])):
                                        print('###', curr_layer, curr_elem, to_vertex, curr_slot, candidate_slot,right_vertex, index_to, index_from)
                                        slot_number = candidate_slot
                                        break

                                else:
                                    # TODO: обработать очень редкую ситуацию, когда нельзя выйти ни из какого слота - всё приведёт к наолжению стрелок
                                    # Здесь HOTFIX, чтобы хотя бы не падало
                                    slot_number = range_slots[-1] + 1
                                    if (curr_elem, to_vertex) in edges_slots:
                                        edges_slots[curr_elem, to_vertex][0] = slot_number
                                    else:
                                        edges_slots[curr_elem, to_vertex] = [slot_number]
                                    continue

                            else: slot_number = curr_slot_from[0]

                            if (curr_elem, to_vertex) in edges_slots:
                                edges_slots[curr_elem, to_vertex][0] = slot_number
                            else:
                                edges_slots[curr_elem, to_vertex] = [slot_number]

                            del curr_slot[curr_slot.index(slot_number)]

                    else:  # Если нормальный элемент соединяется с нормальным

                        index_to = (max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(to_vertex)
                        index_from = (max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(curr_elem)

                        if index_to < index_from:  # Стрелка поедет вверх
                            # !!! Элемент точно не определён

                            curr_slot_from = edges_available_slots_forward[curr_elem]
                            curr_slot_to = edges_available_slots_backward[to_vertex]

                            #slot_number_from = curr_slot_from[0]

                            #print('!!!',  curr_layer, curr_elem, to_vertex, (max_in_layers - len(next_layer)) // 2 + len(next_layer),index_from, (max_in_layers - len(next_layer)) // 2 + 1)

                            if (max_in_layers - len(next_layer)) // 2 + len(next_layer) >= index_from >= (max_in_layers - len(next_layer)) // 2 + 1:  # Если справа есть вершина

                                right_vertex = next_layer[index_from - (max_in_layers - len(next_layer)) // 2 - 1]

                                for candidate_slot in curr_slot_from:

                                    if candidate_slot in edges_available_slots_backward[right_vertex] if isinstance(right_vertex, int) else candidate_slot != 0 or (
                                            index_from < (max_in_layers-len(curr_layer))//2+1+curr_layer.index(right_vertex if right_vertex in curr_layer else right_vertex[0])):

                                        print('###', curr_layer, curr_elem, to_vertex, curr_slot_from, candidate_slot, right_vertex, index_to, index_from)
                                        slot_number_from = candidate_slot
                                        break

                                else:
                                    # TODO: обработать очень редкую ситуацию, когда нельзя выйти ни из какого слота - всё приведёт к наложению стрелок
                                    # Здесь HOTFIX, чтобы хотя бы не падало
                                    slot_number_to = curr_slot_to[-1] if all(i <= 0 for i in curr_slot_to) else [i for i in curr_slot_to if i > 0][0]
                                    edges_slots[curr_elem, to_vertex] = [range_slots[-1] + 1, slot_number_to]
                                    continue

                            else: slot_number_from = curr_slot_from[0]

                            # Выбирается ближайший к нулевому слоту положительный, иначе ближайший к нулевому слоту отрицательный
                            slot_number_to = curr_slot_to[-1] if all(i <= 0 for i in curr_slot_to) else [i for i in curr_slot_to if i > 0][0]

                            edges_slots[curr_elem, to_vertex] = [slot_number_from, slot_number_to]

                            del curr_slot_from[curr_slot_from.index(slot_number_from)]
                            del curr_slot_to[curr_slot_to.index(slot_number_to)]


                        elif index_to > index_from:  # Стрелка поедет вниз
                            # !!! Элемент точно не определён

                            curr_slot_from = edges_available_slots_forward[curr_elem]
                            curr_slot_to = edges_available_slots_backward[to_vertex]

                            if (max_in_layers - len(next_layer)) // 2 + len(next_layer) >= index_from >= (max_in_layers - len(next_layer)) // 2 + 1:  # Если справа есть вершина

                                right_vertex = next_layer[index_from - (max_in_layers - len(next_layer)) // 2 - 1]

                                for candidate_slot in [i for i in curr_slot_from if i > 0] or curr_slot_from[::-1]:

                                    if candidate_slot in edges_available_slots_backward[right_vertex] if isinstance(right_vertex, int) else candidate_slot != 0 or (index_from < (
                                                        max_in_layers - len(curr_layer)) // 2 + 1 + curr_layer.index(right_vertex if right_vertex in curr_layer else right_vertex[0])):
                                        print('###', curr_layer, curr_elem, to_vertex, curr_slot_from, candidate_slot,right_vertex, index_to, index_from)
                                        slot_number_from = candidate_slot
                                        break

                                else:
                                    # TODO: обработать очень редкую ситуацию, когда нельзя выйти ни из какого слота - всё приведёт к наолжению стрелок
                                    # Здесь HOTFIX, чтобы хотя бы не падало
                                    slot_number_to = curr_slot_to[0] if all(i >= 0 for i in curr_slot_to) else [i for i in curr_slot_to if i < 0][-1]
                                    edges_slots[curr_elem, to_vertex] = [range_slots[-1] + 1, slot_number_to]
                                    continue
                            else:
                                slot_number_from = curr_slot_from[0]

                            # Выбирается ближайший к нулевому слоту отрицательный, иначе ближайший к нулевому слоту положительный
                            slot_number_to = curr_slot_to[0] if all(i >= 0 for i in curr_slot_to) else [i for i in curr_slot_to if i < 0][-1]

                            edges_slots[curr_elem, to_vertex] = [slot_number_from, slot_number_to]

                            del curr_slot_from[curr_slot_from.index(slot_number_from)]
                            del curr_slot_to[curr_slot_to.index(slot_number_to)]


        # Корректируем (Там, где всего одна стрелка и она не на середине, ставим её на середину)

        for curr_elem in curr_layer:

            if isinstance(curr_elem, int):

                unused_forward_slots = edges_available_slots_forward[curr_elem]

                if len(unused_forward_slots) == count_of_slots - 1 and 0 in unused_forward_slots:

                    edges_slots[curr_elem, forward_graph[curr_elem][0]][0] = 0

        for curr_elem in next_layer:

            if isinstance(curr_elem, int):

                unused_backward_slots = edges_available_slots_backward[curr_elem]

                if len(unused_backward_slots) == count_of_slots - 1 and 0 in unused_backward_slots:

                    edges_slots[backward_graph[curr_elem][0], curr_elem][1] = 0







    print('USED SLOTS')
    pprint(edges_slots)
    print('FORWARD SLOTS')
    pprint(edges_available_slots_forward)
    print('BACKWARD SLOTS')
    pprint(edges_available_slots_backward)







    #  Просчёт координат вершин и рёбер

    vertex_coords = {i: [0,0] for i in graph}

    curr_x_coord = margin_left_graph
    curr_imaginary_vertex = -1

    all_edges = []

    for index_layer, (curr_layer, next_layer) in enumerate(zip(vertices_by_layers, vertices_by_layers[1:] + vertices_by_layers[0])):

        count_in_layer = len(curr_layer)

        start_height_in_layer = (max_in_layers - count_in_layer) // 2 + 1

        count_of_edges = 0  # Количество ребер в текущем слое, которые будут рендерится как изгибающиеся
        curr_edge = 0

        for index_elem, curr_elem in enumerate(curr_layer):
            if isinstance(curr_elem, list):

                if ( start_height_in_layer + index_elem != (max_in_layers - len(next_layer)) // 2 + 1 +
                    next_layer.index(curr_elem if curr_elem in next_layer else curr_elem[1]) ):

                    count_of_edges += 1
            else:
                for index_next, next_elem in enumerate(forward_graph[curr_elem]):

                    if ( start_height_in_layer + index_elem != (max_in_layers - len(next_layer)) // 2 + 1 +
                                    next_layer.index(next_elem if next_elem in next_layer else [curr_elem, next_elem]) ):

                        count_of_edges += 1

        next_layer_x = curr_x_coord + vertex_width + len_after_start_arrow + len_before_end_arrow + count_of_edges * (
                        len_between_arrows + arrow_width) - len_between_arrows

        dist_between_layers = next_layer_x - curr_x_coord - vertex_width - len_css_triangle

        for index_elem, curr_elem in enumerate(curr_layer):

            if isinstance(curr_elem, list):  # Если стрелка выходит из мнимого элемента

                vertex_coords[curr_imaginary_vertex] = [curr_x_coord, len_between_vertices_in_layer * (start_height_in_layer + index_elem) - vertex_height // 2]

                id_list[curr_imaginary_vertex] = [str(curr_elem[0])+'->'+str(curr_elem[1])]

                to_arrow_x = next_layer_x
                to_arrow_y = len_between_vertices_in_layer * ((max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(curr_elem if curr_elem in next_layer else curr_elem[1])
                                        ) + distance_between_slots * (edges_slots[curr_elem[0], curr_elem[1]][1] if curr_elem[1] in next_layer else 0)

                from_arrow_x = curr_x_coord + vertex_width
                from_arrow_y = vertex_coords[curr_imaginary_vertex][1] + vertex_height // 2

                edge_offset = len_after_start_arrow + curr_edge * (arrow_width + len_between_arrows)

                if from_arrow_y == to_arrow_y:  # Если просто прямая стрелка
                    all_edges += [(curr_elem+[1, from_arrow_x, from_arrow_y, dist_between_layers])]

                elif from_arrow_y > to_arrow_y:  # Если изгибающаяся стрелка вверх
                    all_edges += [(curr_elem+[2, from_arrow_x,
                                              from_arrow_y,
                                              edge_offset + arrow_width,

                                              from_arrow_x + edge_offset,
                                              to_arrow_y,
                                              from_arrow_y - to_arrow_y,

                                              from_arrow_x + edge_offset + arrow_width,
                                              to_arrow_y,
                                              dist_between_layers - edge_offset - arrow_width])]
                    curr_edge += 1

                else: # Если изгибающаяся стрелка вниз
                    all_edges += [(curr_elem+[3,from_arrow_x,
                                              from_arrow_y,
                                              edge_offset + arrow_width,

                                              from_arrow_x + edge_offset,
                                              from_arrow_y + arrow_width,
                                              to_arrow_y - from_arrow_y,

                                              from_arrow_x + edge_offset + arrow_width,
                                              to_arrow_y,
                                              dist_between_layers - edge_offset - arrow_width])]
                    curr_edge += 1

                curr_imaginary_vertex -= 1


            else:  # Если стрелка выходит из нормального элемента

                vertex_coords[curr_elem][0] = curr_x_coord
                vertex_coords[curr_elem][1] = len_between_vertices_in_layer * (start_height_in_layer + index_elem) - vertex_height // 2

                for to_vertex in forward_graph[curr_elem]:

                    to_arrow_x = next_layer_x
                    to_arrow_y = len_between_vertices_in_layer * ((max_in_layers - len(next_layer)) // 2 + 1 + next_layer.index(to_vertex if to_vertex in next_layer else
                                        [curr_elem, to_vertex])) + distance_between_slots * (edges_slots[curr_elem, to_vertex][1] if to_vertex in next_layer else 0)

                    from_arrow_x = curr_x_coord + vertex_width
                    from_arrow_y = vertex_coords[curr_elem][1] + vertex_height // 2 + distance_between_slots * edges_slots[curr_elem, to_vertex][0]

                    edge_offset = len_after_start_arrow + curr_edge * (arrow_width + len_between_arrows)

                    if from_arrow_y == to_arrow_y:  # Если просто прямая стрелка
                        all_edges += [([curr_elem, to_vertex] + [1, from_arrow_x, from_arrow_y, dist_between_layers])]

                    elif from_arrow_y > to_arrow_y:  # Если изгибающаяся стрелка вверх
                        all_edges += [([curr_elem, to_vertex] + [2, from_arrow_x,
                                                    from_arrow_y,
                                                    edge_offset + arrow_width,

                                                    from_arrow_x + edge_offset,
                                                    to_arrow_y,
                                                    from_arrow_y - to_arrow_y,

                                                    from_arrow_x + edge_offset + arrow_width,
                                                    to_arrow_y,
                                                    dist_between_layers - edge_offset - arrow_width])]
                        curr_edge += 1

                    else:  # Если изгибающаяся стрелка вниз
                        all_edges += [([curr_elem, to_vertex] + [3, from_arrow_x,
                                                    from_arrow_y,
                                                    edge_offset + arrow_width,

                                                    from_arrow_x + edge_offset,
                                                    from_arrow_y + arrow_width,
                                                    to_arrow_y - from_arrow_y,

                                                    from_arrow_x + edge_offset + arrow_width,
                                                    to_arrow_y,
                                                    dist_between_layers - edge_offset - arrow_width])]
                        curr_edge += 1

        curr_x_coord = next_layer_x

    print('VERTEX COORDINATES')
    pprint(vertex_coords)
    print('ALL EDGES COORDINATES')
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