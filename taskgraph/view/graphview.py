
def get_edge_list(task_set, node_by_task_id):
    edge_list = {}

    start_points = set()
    end_points = set()

    for task in task_set:
        node_id = node_by_task_id[task.identifier]
        out_relations = task.taskrelation_set.filter(from_task=task.identifier)
        in_relations = task.taskrelation_set.filter(from_task=task.identifier)

        if len(in_relations) == 0 and len(out_relations) != 0:
            end_points.add(node_id)
        elif len(in_relations) != 0 and len(out_relations) == 0:
            start_points.add(node_id)
        if len(in_relations) == 0 and len(out_relations) == 0:
            pass

        if len(out_relations):
            edge_list[node_id] = []
            for out_rel in out_relations:
                edge_list[node_id].append(str(node_by_task_id[out_rel.task_to]))

    return edge_list, start_points, end_points


def get_graph_info(task_set, node_by_task_id, start_points, end_points):
    info = {}

    def add_field_val(add_field):
        if add_field.type == 'CharType':
            return add_field.char
        elif add_field.type == 'TextType':
            if len(add_field.text) > 250:
                return add_field.text[:250] + '...'
            return add_field.text
        elif add_field.type == 'DateField':
            return repr(add_field.date)
        return ''

    for task in task_set:
        node_id = node_by_task_id[task.identifier]

        node_view_type = node_id in start_points and 'StartNode' or node_id in end_points and 'EndNode' or 'MiddlePoint'
        current_node_info = [str(node_id), str(task.identifier), node_view_type]

        if task.assignee.name != '__NONE':
            current_node_info.append(('assignee', task.assignee.name))
        if task.category.name != '__NONE':
            current_node_info.append(('category', task.category.name))
        if task.state.name != '__NONE':
            current_node_info.append(('status', task.state.name))

        for field in task.taskadditionalfield_set.all():
            current_node_info.append((field.name, add_field_val(field)))

        info[str(node_id)] = current_node_info

    return info


def prepare_graph(project):

    node_index_by_task = {}
    tasks = project.task_set.all()

    for ind, task in enumerate(tasks):
        node_index_by_task[task.identifier] = ind

    edge_list, start_points, end_points = get_edge_list(tasks, node_index_by_task)

    info = get_graph_info(tasks, node_index_by_task, start_points, end_points)

    return info, edge_list
