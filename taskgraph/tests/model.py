from taskgraph.model.model import *
from taskgraph.tasktracker.getinterface import get_interface
from .settings import tracker_dummy, tracker_redmine
from django.test import TestCase
from django.db import IntegrityError


class TestTracker(TestCase):

    def create_tracker(self):

        all_trackers = Tracker.objects.all()

        tracker = Tracker.objects.create(url='no-validation', user_name='no-validation',
                                           password='no-validation', type='no-validation')

        from_get_tracker = Tracker.objects.get(url='no-validation')

        self.assertTrue(tracker and from_get_tracker)
        self.assertEqual(tracker, from_get_tracker)

        from_get_tracker.delete()

        all_trackers_after_delete = Tracker.objects.all()

        self.assertEqual(all_trackers, all_trackers_after_delete)

    def test_unique(self):
        Tracker.objects.get_or_create(url='no-validation', user_name='no-validation',
                                      password='no-validation', type='no-validation')
        try:
            Tracker.objects.create(url='no-validation', user_name='no-validation',
                                   password='no-validation', type='no-validation')
        except IntegrityError:
            return

        self.assertTrue(False)

    @staticmethod
    def assert_creation(test_case, models_before):
        for model_type, objects_before in models_before:
            test_case.assertTrue(model_type.objects.all().count() - objects_before > 0)

    @staticmethod
    def assert_cleanup(test_case, models_before):
        for model_type, objects_before in models_before:
            test_case.assertTrue(model_type.objects.all().count() - objects_before == 0)

    @staticmethod
    def test_projects_creation_and_cleanup(test_case, tracker):
        type_list = [Project, Assignee, TaskState, TaskRelationType]

        models_before = []
        for model_type in type_list:
            models_before.append((model_type, model_type.objects.all().count()))

        tracker.restore_project_list(get_interface(tracker.type))

        TestTracker.assert_creation(test_case, models_before)

        tracker.delete()

        TestTracker.assert_cleanup(test_case, models_before)


class TestProject:

    @staticmethod
    def test_create_and_clean_up_tasks(test_case, tracker):
        tracker.restore_project_list(get_interface(tracker.type))

        list_before = []

        task_count = Task.objects.all().count()
        rel_count = TaskRelation.objects.all().count()

        list_before.append((Task, task_count))
        #list_before.append((TaskRelation, rel_count))

        for project in tracker.project_set.all():
            project.is_active = True
            project.save()

        tracker.restore_project_tasks(get_interface(tracker.type))

        for model_type, before_count in list_before:
            test_case.assertTrue(model_type.objects.all().count() - before_count > 0)

        tracker.delete()

        for model_type, before_count in list_before:
            test_case.assertTrue(model_type.objects.all().count() - before_count == 0)


class TestTrackerWithDummy(TestCase):

    def test_projects_creation_and_cleanup(self):
        TestTracker.test_projects_creation_and_cleanup(self, tracker_dummy())


class TestTrackerWithRedmine(TestCase):
    def test_projects_creation_and_cleanup(self):
        if tracker_redmine:
            TestTracker.test_projects_creation_and_cleanup(self, tracker_redmine())


class TestProjectWithDummy(TestCase):
    def test_projects_creation_and_cleanup(self):
        TestProject.test_create_and_clean_up_tasks(self, tracker_dummy())


class TestProjectWithRedmine(TestCase):
    def test_projects_creation_and_cleanup(self):
        if tracker_redmine:
            TestProject.test_create_and_clean_up_tasks(self, tracker_redmine())
