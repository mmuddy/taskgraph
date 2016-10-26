from enum import Enum
import abc


class Action:

    Type = Enum('Type', 'CREATE DELETE CHANGE', module=__name__)

    def __init__(self, obj, action):
        self.obj = obj
        self.type = action


class Project:

    class Meta:
        def __init__(self, assignees, task_categories, relation_types, milestones=None, task_states=None, task_meta=None):
            self.assignees = assignees
            self.task_categories = task_categories
            self.relation_types = relation_types
            self.milestones = milestones
            self.task_states = task_states

    def __init__(self, name, identifier, meta, description=None, child_id_list=None):
        self.name = name
        self.identifier = identifier
        self.description = description
        self.child_id_list = child_id_list
        self.meta = meta


class TrackerInterface:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def connect(self, tracker_inf):
        pass

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abc.abstractmethod
    def refresh(self):
        pass

    @abc.abstractmethod
    def get_projects(self):
        pass

    @abc.abstractmethod
    def get_tasks(self, project_id):
        pass

    @abc.abstractmethod
    def update_task(self, action):
        pass

    @abc.abstractmethod
    def update_relation(self, action):
        pass



