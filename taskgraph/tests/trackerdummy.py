from taskgraph.tasktracker.abstract import TrackerInterface, Project
from datetime import datetime
from random import shuffle, randint


class TrackerDummy(TrackerInterface):

    @staticmethod
    def create_kw_args_set(arg_names, args):
        kw_args_set = []

        for arg_group in args:
            single_kw_arg = {}
            for ind, arg in enumerate(arg_group):
                single_kw_arg[arg_names[ind]] = arg
            kw_args_set.append(single_kw_arg)

        return kw_args_set

    def __init__(self):
        self.tracker_inf = None

        self.assignees = TrackerDummy.create_kw_args_set(['name'],
                                                         [['dev1'], ['dev2'], ['dev3'],
                                                          ['tstr1'], ['tstr2'],
                                                          ['mngr1'], ['mngr2']])

        self.milestones = TrackerDummy.create_kw_args_set(['name', 'date'],
                                                          [('stage1', datetime(year=2016, month=10, day=1)),
                                                           ('stage2', datetime(year=2016, month=11, day=1)),
                                                           ('stage3', datetime(year=2016, month=12, day=1)),
                                                           ('stage4', datetime(year=2017, month=1, day=1))])

        self.task_categories = TrackerDummy.create_kw_args_set(['name'], [['bug'], ['feature'], ['task'], ['question']])
        self.task_states = TrackerDummy.create_kw_args_set(['name'], [['done'], ['assigned'],
                                                                      ['closed'], ['in progress']])
        self.relation_types = TrackerDummy.create_kw_args_set(['name'], [['parent'], ['related'], ['block']])

        self.meta = Project.Meta(assignees=self.assignees, milestones=self.milestones,
                                 task_categories=self.task_categories, task_states=self.task_states,
                                 relation_types=self.relation_types)

        self.tmplt_project = ['Project{}', 'PrjctId{}', 'Description{}']

    def connect(self, tracker_inf):
        self.tracker_inf = tracker_inf
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def refresh(self):
        pass

    def get_projects(self):
        project_list = []

        for ind in range(10):
            project_data = [arg.format(ind) for arg in self.tmplt_project[:-1]]
            project_data.append(self.meta)
            project_list.append(Project(*project_data, description=self.tmplt_project[-1].format(ind)))

        project_list[0].child_id_list = [project_list[1].identifier, project_list[2].identifier,
                                         project_list[3].identifier]

        project_list[2].child_id_list = [project_list[4].identifier, project_list[5].identifier]

        project_list[6].child_id_list = [project_list[7].identifier, project_list[8].identifier,
                                         project_list[9].identifier]

        return project_list

    def get_tasks(self, _):
        task_tmplt = {'identifier': 0, 'assignee': '', 'milestone': '', 'category': '', 'state': ''}
        ids = [x for x in range(100)]
        shuffle(ids)

        task_lst = []

        for ind in range(15):
            new_task = task_tmplt.copy()
            new_task['identifier'] = ids[ind]
            new_task['assignee'] = self.assignees[randint(0, len(self.assignees) - 1)]['name']
            new_task['milestone'] = self.milestones[randint(0, len(self.milestones) - 1)]['name']
            new_task['category'] = self.task_categories[randint(0, len(self.task_categories) - 1)]['name']
            new_task['state'] = self.task_states[randint(0, len(self.task_states) - 1)]['name']
            task_lst.append((new_task, None, []))

        for ind, task_tuple in enumerate(task_lst[:-3]):
            _, _, children = task_tuple
            for child_ind in range(ind + 1, randint(ind + 1, ind + 4)):
                children.append((ids[child_ind], self.relation_types[randint(0, len(self.relation_types) - 1)]['name']))

        return task_lst

    def update_relation(self, action):
        pass

    def update_project(self, action):
        pass
