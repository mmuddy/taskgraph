from django.test import TestCase
from django.test import Client
from taskgraph.model.model import *
from django.core.serializers.json import Serializer

class TaskEditTests(TestCase):

    client = Client()

    def test_incorrect_get_parameters(self):
        response = self.client.get('/taskgraph/task-edit/?some=bullshit')
        self.assertContains(response, text='Incorrect URL')

    def test_not_existing_task_id(self):
        response = self.client.get('/taskgraph/task-edit/?task=4356543')
        self.assertContains(response, text='Task not found')

    def test_post_form(self):
        response = self.client.get('/taskgraph/task-edit/?task=4356543')
        task = Task.objects.all()[0]
        s = Serializer()
        dump = s.serialize(queryset=[task])
        response = self.client.post("/taskgraph/task-edit/?task=" + str(task.identifier),
            {'category': 'bug', 'assignee': 'dev1', 'milestone': 'stage2', 'state': 'assigned'})
        self.assertEqual(response.status_code, 302)
        new_task = Task.objects.all()[0]
        new_dump = s.serialize(queryset=[new_task])
        self.assertTrue(dump != new_dump)