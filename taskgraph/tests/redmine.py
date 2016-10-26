from taskgraph.tasktracker.redmine import IRedmine, Action
from .settings import tracker_redmine
from django.test import TestCase


class Project:
    def __init__(self, name):
        self.name = name


class TestIRedmine(TestCase):

    tracker_inf = tracker_redmine()

    def test_project_list(self):
        with IRedmine().connect(TestIRedmine.tracker_inf) as redmine:
            projects = redmine.get_projects()
            created = [project.name for project in projects if project.name == 'Pytift test']
            self.assertTrue(created and len(created) == 1)

    def test_task_list(self):
        with IRedmine().connect(TestIRedmine.tracker_inf) as redmine:
            projects = redmine.get_projects()
            created = [project for project in projects if project.name == 'Pytift test']
            self.assertTrue(created and len(created) == 1)
            pytiff_id = created[0].identifier
            tasks = redmine.get_tasks(pytiff_id)
            self.assertTrue(tasks)
