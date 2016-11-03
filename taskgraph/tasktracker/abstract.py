from enum import Enum
import abc


class Action:

    Type = Enum('Type', 'CREATE DELETE CHANGE', module=__name__)

    def __init__(self, obj, action):
        self.obj = obj
        self.type = action


class Task:

    AdditionalFieldType = Enum('AdditionalFieldType', 'CharField TextField DateField', module=__name__)

    def __init__(self):
        self.identifier = None
        self.project_identifier = None
        self.assignee = None
        self.milestone = None
        self.category = None
        self.status = None

        self.additional_fields = []

    @staticmethod
    def additional_field_as_arg(add_field):
        if add_field['type'] == 'CharField':
            return {add_field['name']: add_field['char']}
        if add_field['type'] == 'CharField':
            return {add_field['name']: add_field['char']}
        if add_field['type'] == 'TextField':
            return {add_field['name']: add_field['text']}
        if add_field['type'] == 'DateField':
            return {add_field['name']: add_field['date']}
        raise AttributeError

    def add_char_field(self, name, value):
        self.additional_fields.append({'name': name, 'type': 'CharField', 'char': value})

    def add_text_field(self, name, value):
        self.additional_fields.append({'name': name, 'type': 'TextField', 'text': value})

    def add_date_field(self, name, value):
        self.additional_fields.append({'name': name, 'type': 'DateField', 'date': value})

    def regular_fields_as_dict(self):
        d = {}

        if self.identifier:
            d['identifier'] = self.identifier
        if self.assignee:
            d['assignee'] = {'name': self.assignee[0], 'identifier': self.assignee[1]}
        if self.milestone:
            d['milestone'] = {'name': self.milestone[0]}
        if self.category:
            d['category'] = {'name': self.category[0], 'identifier': self.category[1]}
        if self.status:
            d['state'] = {'name': self.status[0], 'identifier': self.status[1]}

        return d


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

    @abc.abstractmethod
    def my_name(self):
        pass



