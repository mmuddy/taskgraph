from taskgraph.tasktracker.abstract import TrackerInterface, Project, Action, Task
from redmine import Redmine, ForbiddenError

from copy import deepcopy


class IRedmine(TrackerInterface):

    def __init__(self):
        self.tracker_inf = None
        self.redmine = None

        self.user_by_project = {}
        self.status_by_id = {}
        self.states_args = []
        self.categories_by_project = {}

        self.relation_types = ('relates', 'duplicates', 'duplicated', 'blocks', 'blocked',
                               'precedes', 'follows', 'copied_to', 'copied_from', 'parent')
        self.relation_args = [{'name': rel_type} for rel_type in self.relation_types]

        self.current_name = ''
        self.current_id = None

    def __enter__(self):
        self.refresh()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def connect(self, tracker_inf):
        self.tracker_inf = tracker_inf
        return self

    def refresh(self):
        self.redmine = Redmine(self.tracker_inf.url, username=self.tracker_inf.user_name,
                               password=self.tracker_inf.password)
        self.current_name = self.redmine.user.get('current').name
        self.current_id = self.redmine.user.get('current').id

    def get_projects(self):
        self.user_by_project.clear()
        self.status_by_id.clear()
        self.states_args.clear()
        self.categories_by_project.clear()

        for issue_status in self.redmine.issue_status.all():
            self.status_by_id[issue_status.id] = issue_status.name
            self.states_args.append({'name': issue_status.name})

        redmine_projects = self.redmine.project.all(include='issue_categories')

        project_list = []
        project_identifier_by_id = {}
        parent_id_by_child = {}
        project_by_identifier = {}

        for project in redmine_projects:
            project_identifier_by_id[project.id] = project.identifier

            self.user_by_project[project.identifier] = {}
            user_by_id = self.user_by_project[project.identifier]
            assignee = []
            for project_membership in self.redmine.project_membership.filter(project_id=project.identifier):
                user_by_id[project_membership.user.id] = project_membership.user.name
                if project_membership.user.id == self.current_id:
                    user_by_id['current'] = self.current_id
                assignee.append({'name': project_membership.user.name})

            if hasattr(project, 'parent_id') and project.parent_id != -1:
                parent_id_by_child[project.identifier] = project.parent_id

            self.categories_by_project[project.identifier] = {}
            category = self.categories_by_project[project.identifier]
            categories = []

            try:
                for issue_category in self.redmine.issue_category.filter(project_id=project.identifier):
                    category[issue_category.id] = issue_category.name
                    categories.append({'name': issue_category.name})
            except ForbiddenError:
                categories = None

            meta = Project.Meta(assignee, categories, self.relation_args, task_states=self.states_args)

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

        current_id = self.redmine.user.get('current').id
        user_by_id = self.user_by_project.get(project_id)
        member = current_id in user_by_id or []

        for task in self.redmine.issue.filter(project_id=project_id):
            new_task = Task()
            new_task.identifier = task.id
            new_task.project_identifier = project_id

            if hasattr(task, 'assigned_to'):
                new_task.assignee = task.assigned_to.name
            if hasattr(task, 'status'):
                new_task.status = task.status.name
            if hasattr(task, 'category'):
                new_task.category = task.category.name

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

            if not member:
                continue

            try:
                for relation in self.redmine.issue_relation.filter(issue_id=task.id):
                    if relation.issue_id == task.id:
                        related_tasks.append((relation.issue_to_id, relation.relation_type))
            except ForbiddenError:
                pass

        return task_list

    def update_task(self, action):
        if action.type == Action.Type.CREATE:
            self.redmine.issue.create(action.obj.project_identifier, **self._translate_task_object(action.obj))
        elif action.type == Action.Type.CHANGE:
            self.redmine.issue.update(action.obj.identifier, **self._translate_task_object(action.obj))
        elif action.type == Action.Type.DELETE:
            self.redmine.issue.delete(action.obj.identifie)

    def update_relation(self, action):
        to_id = action.obj.to_task.identifier
        from_id = action.obj.from_task.identifier
        rel_type = action.obj.type.name

        if action.type == Action.Type.CREATE:
            relation = self.redmine.issue_relation.new()
            relation.issue_id = from_id
            relation.issue_to_id = to_id
            relation.relation_type = rel_type
            relation.save()
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
            self.redmine.issue_relation.delete(requested.id)

    def my_name(self):
        return self.current_name

    def _user_by_project(self, project_id):
        return self.user_by_project.get(project_id) or {}

    def _user_id_by_name(self, project_id, user_name):
        for user_id, name in self._user_by_project(project_id).items():
            if name == user_name:
                return user_id
        return None

    def _category_by_project(self, project_id):
        return self.categories_by_project.get(project_id) or {}

    def _category_id_by_name(self, project_id, name):
        for category_id, category_name in self._category_by_project(project_id).items():
            if category_name == name:
                return category_id
        return None

    def _status_id_by_name(self, name):
        for status_id, status_name in self.status_by_id.items():
            if status_name == name:
                return status_id
        return None

    def _translate_task_object(self, obj):
        d = {}

        if obj.assignee:
            d['assigned_to'] = self._user_id_by_name(obj.project_identifier, obj.assignee)
        """if obj.milestone:
            d['milestone'] = obj.milestone"""
        if obj.category:
            d['category'] = self._category_id_by_name(obj.project_identifier, obj.category)
        if obj.status:
            d['status'] = self._status_id_by_name(obj.status)

        for add_field in obj.additional_fields:
            d.update(Task.additional_field_as_arg(add_field))

        dc = deepcopy(d)
        for key, val in d.items():
            if not val:
                dc.pop(key)

        return dc
