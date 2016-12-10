from taskgraph.tasktracker.abstract import TrackerInterface, Project, Action, Task
from taskgraph.tasktracker import abstract

from redmine import Redmine, ForbiddenError
from redmine.packages.requests.exceptions import ConnectionError
from redmine.exceptions import AuthError
from copy import deepcopy


class IRedmine(TrackerInterface):

    def __init__(self):
        self.tracker_inf = None
        self.redmine = None

        self.relation_types = ('relates', 'duplicates', 'duplicated', 'blocks', 'blocked',
                               'precedes', 'follows', 'copied_to', 'copied_from', 'parent')

        self.reversed_relations = {'duplicated', 'blocked', 'follows', 'copied_from'}
        self.r_relations_replacements = {'duplicated': 'duplicates',
                                         'blocked': 'blocks',
                                         'follows': 'precedes',
                                         'copied_from': 'copied_to'}

        self.relation_args = [{'name': rel_type} for rel_type in self.relation_types]

        self.current_name = ''
        self.current_id = None

    def __enter__(self):
        try:
            self.refresh()
        except (ConnectionError, AuthError) as e:
            raise abstract.ConnectionError(e)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def connect(self, tracker_inf):
        self.tracker_inf = tracker_inf
        return self

    def relation_type(self, relation_type):
        if relation_type in self.r_relations_replacements.keys():
            return False, self.r_relations_replacements[relation_type]
        return True, relation_type

    def refresh(self):
        self.redmine = Redmine(self.tracker_inf.url, username=self.tracker_inf.user_name,
                               password=self.tracker_inf.password)
        self.current_name = self.redmine.user.get('current').name
        self.current_id = self.redmine.user.get('current').id

    def get_projects(self):
        states_args = []

        for issue_status in self.redmine.issue_status.all():
            states_args.append({'name': issue_status.name, 'identifier': issue_status.id})

        redmine_projects = self.redmine.project.all(include='issue_categories')

        project_list = []
        project_identifier_by_id = {}
        parent_id_by_child = {}
        project_by_identifier = {}

        for project in redmine_projects:
            project_identifier_by_id[project.id] = project.identifier

            assignee = []
            for project_membership in self.redmine.project_membership.filter(project_id=project.identifier):
                assignee.append({'name': project_membership.user.name, 'identifier': project_membership.user.id})

            if hasattr(project, 'parent_id') and project.parent_id != -1:
                parent_id_by_child[project.identifier] = project.parent_id

            categories = []

            try:
                for issue_category in self.redmine.issue_category.filter(project_id=project.identifier):
                    categories.append({'name': issue_category.name, 'identifier': issue_category.id})
            except ForbiddenError:
                categories = None

            meta = Project.Meta(assignee, categories, self.relation_args, task_states=states_args)

            project_list.append(Project(name=project.name, identifier=project.identifier,
                                        description=project.description, meta=meta, child_id_list=[]))
            project_by_identifier[project_list[-1].identifier] = project_list[-1]

        for project in project_list:
            child_id = project.identifier
            parent_id = parent_id_by_child.get(project.identifier)

            if parent_id:
                parent_identifier = project_identifier_by_id[parent_id]
                parent = project_by_identifier[parent_identifier]
                parent.child_id_list.append(child_id)

        return project_list

    def get_tasks(self, project_id):
        task_list = []

        for task in self.redmine.issue.filter(project_id=project_id):
            new_task = Task()
            new_task.identifier = task.id
            new_task.project_identifier = project_id

            if hasattr(task, 'assigned_to'):
                new_task.assignee = (task.assigned_to.name, task.assigned_to.id)
            if hasattr(task, 'status'):
                new_task.status = (task.status.name, task.status.id)
            if hasattr(task, 'category'):
                new_task.category = (task.category.name, task.category.id)

            if hasattr(task, 'subject'):
                new_task.add_char_field('subject', task.subject)
            if hasattr(task, 'description'):
                new_task.add_text_field('description', task.description)
            if hasattr(task, 'start_date'):
                new_task.add_date_field('start_date', task.start_date)
            if hasattr(task, 'due_date'):
                new_task.add_date_field('due_date', task.due_date)

            related_tasks = []
            task_list.append((new_task, new_task.additional_fields, related_tasks))

            try:
                for relation in self.redmine.issue_relation.filter(issue_id=task.id):
                    if relation.issue_id == task.id:
                        related_tasks.append((relation.issue_to_id, relation.relation_type))
            except ForbiddenError:
                pass

        return task_list

    def update_task(self, action):
        if action.type == Action.Type.CREATE:
            res = self.redmine.issue.create(action.obj.identifier, **self._translate_task_object(action.obj))
            if not res:
                raise abstract.SaveError('Create task with id %s failed' % action.obj.identifier)
        elif action.type == Action.Type.CHANGE:
            res = self.redmine.issue.update(action.obj.identifier, **self._translate_task_object(action.obj))
            if not res:
                raise abstract.SaveError('Update task with id %s failed' % action.obj.identifier)
        elif action.type == Action.Type.DELETE:
            res = self.redmine.issue.delete(action.obj.identifie)
            if not res:
                raise abstract.SaveError('Create task with id %s failed' % action.obj.identifier)

    def update_relation(self, action):
        to_id = action.obj.to_task.identifier
        from_id = action.obj.from_task.identifier
        rel_type = action.obj.type.name

        if action.type == Action.Type.CREATE:
            relation = self.redmine.issue_relation.new()
            relation.issue_id = from_id
            relation.issue_to_id = to_id
            relation.relation_type = rel_type
            res = relation.save()
            if not res:
                raise abstract.SaveError('Create relation from %i to %i failed' % (from_id, to_id))
        elif action.type == Action.Type.CHANGE:
            raise NotImplementedError
        elif action.type == Action.Type.DELETE:
            issue = self.redmine.issue.get(from_id)
            requested = None
            for rel in issue.relations:
                if rel.issue_to_id == to_id and rel.relation_type == rel_type:
                    requested = rel
                    break
            if not requested:
                raise KeyError
            res = self.redmine.issue_relation.delete(requested.id)
            if not res:
                raise abstract.SaveError('Delete relation from %i to %i failed' % (from_id, to_id))

    def my_name(self):
        return self.current_name

    @staticmethod
    def _translate_task_object(obj):
        d = {}

        if obj.assignee:
            d['assigned_to_id'] = obj.assignee
        """if obj.milestone:
            d['milestone'] = obj.milestone"""
        if obj.category:
            d['category_id'] = obj.category
        if obj.status:
            d['status_id'] = obj.status

        for add_field in obj.additional_fields:
            d.update(Task.additional_field_as_arg(add_field))

        dc = deepcopy(d)
        for key, val in d.items():
            if not val:
                dc.pop(key)

        return dc
