from taskgraph.tasktracker.abstract import TrackerInterface, Action, Project
from redmine import Redmine, ForbiddenError


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

    def __enter__(self):
        self.refresh()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.redmine = None

    def connect(self, tracker_inf):
        self.tracker_inf = tracker_inf
        return self

    def refresh(self):
        self.redmine = Redmine(self.tracker_inf.url, username=self.tracker_inf.user_name,
                               password=self.tracker_inf.password)
        self.states_args.clear()

        for issue_status in self.redmine.issue_status.all():
            self.status_by_id[issue_status.id] = issue_status.name
            self.states_args.append({'name': issue_status.name})

    def get_projects(self):
        redmine_projects = self.redmine.project.all()

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
                assignee.append({'name': project_membership.user.name})

            if hasattr(project, 'parent_id') and project.parent_id != -1:
                parent_id_by_child[project.identifier] = project.parent_id
            """self.categories_by_project[project.identifier] = {}
            category = self.categories_by_project[project.identifier]
            for issue_status in self.redmine.issue_category.filter(project_id=project.identifier):
                category[issue_status.id] = issue_status.name"""

            meta = Project.Meta(assignee, None, self.relation_args, task_states=self.states_args)

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
        member = current_id in self.user_by_project[project_id].keys()

        for task in self.redmine.issue.filter(project_id=project_id):
            new_task = dict()
            new_task['identifier'] = task.id

            if hasattr(task, 'assigned_to'):
                new_task['assignee'] = task.assigned_to.name
            if hasattr(task, 'status'):
                new_task['category'] = task.status.name

            additional_fields = []

            if hasattr(task, 'subject'):
                additional_fields.append({'name': 'subject', 'type': 'CharField', 'char': task.subject})
            if hasattr(task, 'description'):
                additional_fields.append({'name': 'description', 'type': 'TextField', 'text': task.description})
            if hasattr(task, 'start_date'):
                additional_fields.append({'name': 'start_date', 'type': 'DateField', 'date': task.start_date})
            if hasattr(task, 'due_date'):
                additional_fields.append({'name': 'due_date', 'type': 'DateField', 'date': task.due_date})

            related_tasks = []

            if not member:
                task_list.append((new_task, additional_fields, related_tasks))
                continue

            try:
                for relation in self.redmine.issue_relation.filter(issue_id=task.id):
                    related_tasks.append((relation.issue_to_id, relation.relation_type))
            except ForbiddenError:
                related_tasks = None

            task_list.append((new_task, additional_fields, related_tasks))

        return task_list

    def update_task(self, action):
        pass

    def update_relation(self, action):
        pass