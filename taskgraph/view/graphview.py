from taskgraph.model.model import TaskRelation

from tulip import *

from json import dumps
from math import sqrt, pow


def get_edge_list(task_set, node_by_task_id, i_tracker):
    task_set_len = len(task_set)

    edge_list = {}
    adjacency_matrix = [[('', 0) for _ in range(0, task_set_len)] for _ in range(0, task_set_len)]
    start_points = set()
    end_points = set()

    for task in task_set:
        node_id = node_by_task_id[task.identifier]
        out_relations = TaskRelation.objects.filter(project__identifier=task.project.identifier,
                                                    from_task__identifier=task.identifier)
        in_relations = TaskRelation.objects.filter(project__identifier=task.project.identifier,
                                                   to_task__identifier=task.identifier)

        if len(in_relations) == 0 and len(out_relations) != 0:
            end_points.add(node_id)
        elif len(in_relations) != 0 and len(out_relations) == 0:
            start_points.add(node_id)
        if len(in_relations) == 0 and len(out_relations) == 0:
            pass

        if len(out_relations) == 0:
            continue

        edge_list[node_id] = []
        for out_rel in out_relations:
            rel_type = out_rel.type.name

            direct, rel_type_name = i_tracker.relation_type(rel_type)
            related_id = node_by_task_id[out_rel.to_task.identifier]

            if direct:
                edge_list[node_id].append(related_id)
                adjacency_matrix[int(node_id)][int(related_id)] = (rel_type_name, out_rel.id)
                continue

            adjacency_matrix[int(related_id)][int(node_id)] = (rel_type_name, out_rel.id)
            if related_id in edge_list.keys():
                edge_list[related_id].append(node_id)
            else:
                edge_list[related_id] = [node_id]

    return edge_list, adjacency_matrix, start_points, end_points


def get_graph_info(task_set, node_by_task_id, start_points, end_points):
    info = {}

    def add_field_val(add_field):
        if add_field.type == 'CharField':
            return add_field.char
        elif add_field.type == 'TextField':
            if len(add_field.text) > 250:
                return dumps(add_field.text[:250] + '...')
            return dumps(add_field.text)
        elif add_field.type == 'DateField':
            return add_field.date.strftime("%Y-%m-%d")
        return ''

    for task in task_set:
        node_id = node_by_task_id[task.identifier]

        node_view_type = node_id in start_points and 'StartNode' or node_id in end_points and 'EndNode' or 'MiddlePoint'
        current_node_info = [node_id, str(task.identifier), node_view_type]

        additional = []

        if task.assignee.name != '__NONE':
            additional.append(('assignee', task.assignee.name))
        if task.category.name != '__NONE':
            additional.append(('category', task.category.name))
        if task.state.name != '__NONE':
            additional.append(('status', task.state.name))

        for field in task.taskadditionalfield_set.all():
            additional.append((field.name.replace("_", " "), add_field_val(field)))
        current_node_info.append(additional)

        info[node_id] = current_node_info

    return info


def prepare_graph(project, i_tracker):

    node_index_by_task = {}
    tasks = project.task_set.all()

    for ind, task in enumerate(tasks):
        node_index_by_task[task.identifier] = str(ind)

    edge_list, adjacency_matrix, start_points, end_points = get_edge_list(tasks, node_index_by_task, i_tracker)

    info = get_graph_info(tasks, node_index_by_task, start_points, end_points)

    return info, edge_list, adjacency_matrix


def prepare_tultip(info, edge_list, vertex_block_width=1, vertex_block_height=1):
    tgraph = tlp.newGraph()

    tulip_graph = {}

    node_ind = {}
    for i in info.keys():
        node = tgraph.addNode()
        node_ind[node] = i
        tulip_graph[node] = info[i]
        info[i] += [node]

    for i in edge_list:
        for j in edge_list[i]:
            tgraph.addEdge(info[i][-1], info[j][-1])

    view_size = tgraph.getSizeProperty("viewSize")
    view_shape = tgraph.getIntegerProperty("viewShape")

    for n in tgraph.getNodes():
        view_size[n] = tlp.Size(vertex_block_width, vertex_block_height, 1)
        view_shape[n] = tlp.NodeShape.Square

    return tgraph, node_ind


def normalize_graph_coords(tgraph, vertex_block_height, node_ind, scale_index):
    node_dists = []
    node_list = [node for node in tgraph.getNodes()]

    for node_i in node_list:
        for node_j in node_list[1:int(len(node_list) / 2)]:
            node_i_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_i)
            node_j_value = tgraph.getLayoutProperty("viewLayout").getNodeValue(node_j)
            dist = sqrt(pow(node_i_value[0] - node_j_value[0], 2) +
                        pow(node_i_value[1] - node_j_value[1], 2))
            if dist:
                node_dists.append(dist)

    ideal_dist = vertex_block_height * scale_index
    min_dist = min(node_dists)
    proportion = ideal_dist / min_dist

    coords = []
    for node in tgraph.getNodes():
        coords.append((node_ind[node],
                       tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[0] * proportion,
                       tgraph.getLayoutProperty("viewLayout").getNodeValue(node)[1] * proportion))

    return coords
