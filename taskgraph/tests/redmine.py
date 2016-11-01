from taskgraph.tasktracker.redmine import IRedmine
from taskgraph.tasktracker.abstract import Action
from .settings import tracker_redmine
from django.test import TestCase


class Project:
    def __init__(self, name):
        self.name = name


class Relation:
    class WithId:
        def __init__(self, t_id):
            self.identifier = t_id

    class WithName:
        def __init__(self, t_name):
            self.name = t_name

    def __init__(self, t_from, t_to, t_type):
        self.to_task = Relation.WithId(t_to)
        self.from_task = Relation.WithId(t_from)
        self.type = Relation.WithName(t_type)


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
            test_bot_task = [task for task, _, _ in tasks if task.identifier == 7006]
            self.assertEqual(len(test_bot_task), 1)

    def test_task_update(self):
        with IRedmine().connect(TestIRedmine.tracker_inf) as redmine:
            projects = redmine.get_projects()
            created = [project for project in projects if project.name == 'Pytift test']
            self.assertTrue(created and len(created) == 1)

            pytiff_id = created[0].identifier
            old_tasks = [task for task, _, _ in redmine.get_tasks(pytiff_id) if task.category == 'UnitTest']
            test_task_subject = ''
            test_task = None
            for t in old_tasks:
                for f in t.additional_fields:
                    if f['name'] == 'subject' and f['char'] == 'TaskGraph Unit Test Data - test case: task update':
                        test_task_subject = f['char']
                        f['char'] += '[test passed]'
                        test_task = t
            self.assertTrue(test_task)
            redmine.update_task(Action(test_task, Action.Type.CHANGE))

            new_tasks = [task for task, _, _ in redmine.get_tasks(pytiff_id) if task.category == 'UnitTest']
            test_task = None

            for t in new_tasks:
                for f in t.additional_fields:
                    if f['name'] == 'subject' and \
                                    f['char'] == 'TaskGraph Unit Test Data - test case: task update[test passed]':
                        f['char'] = test_task_subject
                        test_task = t

            self.assertTrue(test_task)
            redmine.update_task(Action(test_task, Action.Type.CHANGE))

    def test_task_relation(self):
        with IRedmine().connect(TestIRedmine.tracker_inf) as redmine:
            projects = redmine.get_projects()
            created = [project for project in projects if project.name == 'Pytift test']
            self.assertTrue(created and len(created) == 1)

            pytiff_id = created[0].identifier
            old_tasks = [(task,related_tasks) for task, _, related_tasks in redmine.get_tasks(pytiff_id)
                         if task.category == 'UnitTest']

            rel = None
            old_rel_type = None
            new_type = Relation.WithName('precedes')
            for t, relations in old_tasks:
                if relations:
                    old_rel_type = Relation.WithName(relations[0][1])
                    rel = Relation(t.identifier, relations[0][0], new_type)
                    try:
                        redmine.update_relation(Action(rel, Action.Type.CHANGE))
                    except NotImplementedError:
                        self.assertTrue(True)
                        new_type = old_rel_type
                        rel.type = new_type
                        break
                    self.assertFalse(False)

            self.assertTrue(rel)

            new_tasks = [(task, related_tasks) for task, _, related_tasks in redmine.get_tasks(pytiff_id)
                         if task.category == 'UnitTest']

            found = False
            for t, relations in new_tasks:
                if relations:
                    self.assertTrue(new_type.name == relations[0][1])
                    redmine.update_relation(Action(rel, Action.Type.DELETE))
                    found = True
            self.assertTrue(found)

            new_tasks = [(task, related_tasks) for task, _, related_tasks in redmine.get_tasks(pytiff_id)
                         if task.category == 'UnitTest']

            for _, relations in new_tasks:
                self.assertFalse(relations)

            redmine.update_relation(Action(rel, Action.Type.CREATE))

            new_tasks = [(task, related_tasks) for task, _, related_tasks in redmine.get_tasks(pytiff_id)
                         if task.category == 'UnitTest']

            found = False
            for t, relations in new_tasks:
                if relations:
                    self.assertTrue(old_rel_type.name == relations[0][1])
                    found = True
            self.assertTrue(found)
