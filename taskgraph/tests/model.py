from taskgraph.model.model import *
from taskgraph.tasktracker.getinterface import get_interface
from .settings import tracker_dummy, tracker_redmine
from django.test import TestCase
from django.db import IntegrityError


class TestTracker(TestCase):

    def create_tracker(self):

        all_trackers = Tracker.objects.all()

        tracker = Tracker.objects.create(url='no-validation', type='no-validation')

        from_get_tracker = Tracker.objects.get(url='no-validation')

        self.assertTrue(tracker and from_get_tracker)
        self.assertEqual(tracker, from_get_tracker)

        from_get_tracker.delete()

        all_trackers_after_delete = Tracker.objects.all()

        self.assertEqual(len(all_trackers), len(all_trackers_after_delete))

    def test_unique(self):
        Tracker.objects.get_or_create(url='no-validation', type='no-validation')
        try:
            Tracker.objects.create(url='no-validation', type='no-validation')
        except IntegrityError:
            return

        self.assertTrue(False)


def assert_creation(test_case, models_before):
    for model_type, objects_before in models_before:
        test_case.assertTrue(model_type.objects.all().count() - objects_before > 0)


def assert_cleanup(test_case, models_before):
    for model_type, objects_before in models_before:
        print model_type
        test_case.assertTrue(model_type.objects.all().count() - objects_before == 0)


def test_projects_creation_and_cleanup(test_case, tracker):
    type_list = [Project, Assignee, TaskState, TaskRelationType, TaskCategory]

    models_before = []
    for model_type in type_list:
        models_before.append((model_type, model_type.objects.all().count()))

    tracker.restore_project_list(get_interface(tracker.type))

    assert_creation(test_case, models_before)

    tracker.delete()

    # assert_cleanup(test_case, models_before)


def test_create_and_clean_up_tasks(test_case, tracker):
    i_tracker = get_interface(tracker.type).connect(tracker)
    i_tracker.refresh()

    tracker.restore_project_list(i_tracker)

    list_before = []

    task_count = Task.objects.all().count()
    rel_count = TaskRelation.objects.all().count()

    list_before.append((Task, task_count))
    list_before.append((TaskRelation, rel_count))

    for project in tracker.projects:
        project.is_active = True
        project.save()

    tracker.restore_project_tasks(i_tracker, only_active=False)

    for model_type, before_count in list_before:
        test_case.assertTrue(model_type.objects.all().count() - before_count > 0)

    tracker.delete()

    #for model_type, before_count in list_before:
    #    test_case.assertTrue(model_type.objects.all().count() - before_count == 0)


class TestTrackerWithDummy(TestCase):

    def test_projects_creation_and_cleanup(self):
        test_projects_creation_and_cleanup(self, tracker_dummy())


class TestTrackerWithRedmine(TestCase):
    def test_projects_creation_and_cleanup(self):
        test_projects_creation_and_cleanup(self, tracker_redmine())


class TestProjectWithDummy(TestCase):
    def test_projects_creation_and_cleanup(self):
        test_create_and_clean_up_tasks(self, tracker_dummy())


class TestProjectWithRedmine(TestCase):
    def test_projects_creation_and_cleanup(self):
        test_create_and_clean_up_tasks(self, tracker_redmine())


class TestIntegrationWithRedmine(TestCase):

    def test_task_update(self):
        tracker = tracker_redmine()
        tracker.save()

        i_tracker = get_interface(tracker.type)
        i_tracker.connect(tracker)
        i_tracker.refresh()

        tracker.restore_project_list(get_interface(tracker.type))

        pytiff = None

        for project in tracker.projects:
            if project.name == 'Pytift test':
                project.is_active = True
                project.save()
                pytiff = project
                break

        tracker.restore_project_tasks(get_interface(tracker.type))

        for task in filter(lambda t: t.category.name == 'UnitTest', pytiff.tasks):
            subj_field = filter(lambda f: f.name == 'subject', task.additional_field)[0]
            subj_field.char += '$ test passed'
            subj_field.save()
            task.save(save_on_tracker=True, i_tracker=i_tracker)

        tracker.restore_project_tasks(get_interface(tracker.type))
        pytiff = filter(lambda p: p.name == 'Pytift test', tracker.projects)[0]

        for task in filter(lambda t: t.category.name == 'UnitTest', pytiff.tasks):
            subj_field = filter(lambda f: f.name == 'subject', task.additional_field)[0]
            subj_field.char = subj_field.char.split('$')[0]
            subj_field.save()
            task.save(save_on_tracker=True, i_tracker=i_tracker)

    def test_relation_update(self):
        tracker = tracker_redmine()
        tracker.save()

        i_tracker = get_interface(tracker.type)
        i_tracker.connect(tracker)
        i_tracker.refresh()

        tracker.restore_project_list(get_interface(tracker.type))

        pytiff = None

        for project in tracker.projects:
            if project.name == 'Pytift test':
                project.is_active = True
                project.save()
                pytiff = project
                break

        tracker.restore_project_tasks(get_interface(tracker.type))

        t_from = None
        t_to = None
        t_type = None

        old_count = len(pytiff.tasks_relations)

        for relation in pytiff.tasks_relations:
            t_from = relation.from_task
            t_to = relation.to_task
            t_type = relation.type
            relation.delete(i_tracker=i_tracker)
            break

        self.assertTrue(t_from and t_to and t_type)
        self.assertEqual(len(pytiff.tasks_relations), old_count - 1)

        tracker.restore_project_tasks(get_interface(tracker.type))

        pytiff = filter(lambda p: p.name == 'Pytift test', tracker.projects)[0]

        self.assertEqual(len(pytiff.tasks_relations), old_count - 1)

        t_type = filter(lambda p: p.name == t_type.name, pytiff.task_relation_types)[0]
        t_from = filter(lambda p: p.identifier == t_from.identifier, pytiff.tasks)[0]
        t_to = filter(lambda p: p.identifier == t_to.identifier, pytiff.tasks)[0]

        old_rel = TaskRelation.objects.create(project=pytiff, type=t_type, from_task=t_from, to_task=t_to)
        old_rel.save(i_tracker=i_tracker)

        self.assertEqual(len(pytiff.tasks_relations), old_count)


