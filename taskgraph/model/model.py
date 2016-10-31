from django.db import models

from enum import Enum
from datetime import date


class ChoicesHelper:

    @staticmethod
    def get_choices(cls):
        return ((attr_value.value, attr,) for attr, attr_value in cls.__dict__.items() if not attr.startswith('_'))

    @staticmethod
    def max_length(cls):
        return len(max(ChoicesHelper.get_choices(cls), key=lambda tpl: tpl))

    @staticmethod
    def char_field_with_choices(enm_cls):
        return models.CharField(max_length=ChoicesHelper.max_length(enm_cls),
                                choices=ChoicesHelper.get_choices(enm_cls))


class Tracker(models.Model):

    class Supported(Enum):
        Redmine = 0

    class Meta:
        unique_together = (('user_name', 'url', 'type'),)

    user_name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    type = ChoicesHelper.char_field_with_choices(Supported)

    def __str__(self):
        return 'user_name:{} password:{} url:{} type:{}'.format(self.user_name, self.password, self.url, self.type)

    def __hash__(self):
        return hash('{}{}{}'.format(self.url, self.user_name, self.type))

    def restore_project_list(self, i_tracker):
        with i_tracker.connect(self):
            for deprecated_project in self.project_set.all():
                deprecated_project.delete()

            project_list = i_tracker.get_projects()

            new_projects_lst = []
            for new_project in project_list:
                project_model = Project(tracker=self, identifier=new_project.identifier,
                                        name=new_project.name, description=new_project.description)
                project_model.restore_meta(new_project)
                project_model.save()
                new_projects_lst.append((project_model, new_project))

            for model, project in new_projects_lst:
                model.restore_children(project)
                model.save()

    def restore_project_tasks(self, i_tracker):
        active_project_list = self.project_set.filter(is_active__exact=True)

        if not active_project_list:
            return

        with i_tracker.connect(self):
            for project in active_project_list:
                project.restore_project_tasks(i_tracker)


class Project(models.Model):

    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
    identifier = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=False)

    def restore_meta(self, project_from_tracker):
        self._restore_meta(Milestone, project_from_tracker.meta.milestones, self.milestone_set.all())
        self._restore_meta(Assignee, project_from_tracker.meta.assignees, self.assignee_set.all())
        self._restore_meta(TaskCategory, project_from_tracker.meta.task_categories, self.taskcategory_set.all())
        self._restore_meta(TaskState, project_from_tracker.meta.task_states, self.taskstate_set.all())
        self._restore_meta(TaskRelationType, project_from_tracker.meta.relation_types, self.taskrelationtype_set.all())

    def restore_children(self, project_from_tracker):
        current_children = self.get_child_list()

        for deprecated in current_children:
            deprecated.delete()

        if not project_from_tracker.child_id_list:
            return

        for child_id in project_from_tracker.child_id_list:
            child_model = self.tracker.project_set.all().get(identifier__exact=child_id)
            ProjectRelation.objects.create(tracker=self.tracker, parent=self, child=child_model)

    def get_child_list(self):
        return [relation.child for relation in
                self.tracker.projectrelation_set.filter(parent__identifier__exact=self.identifier)]

    def restore_project_tasks(self, i_tracker):
        for task in self.task_set.all():
            task.delete()
        tasks = i_tracker.get_tasks(self.identifier)
        for task, additional, task_children in tasks:
            self._create_task(task, additional).save()

        for rel in self.taskrelation_set.all():
            rel.delete()

        for task, _, task_children in tasks:
            for child_id, rel_type in task_children or []:
                self._create_relation(task['identifier'], child_id, rel_type)

    def _restore_meta(self, cls_model, new_model_data, old_model_set):
        if not new_model_data:
            return

        for deprecated_model in old_model_set:
            deprecated_model.delete()

        for new_model in new_model_data:
            if new_model:
                cls_model.objects.get_or_create(**new_model, project=self)

    def _create_relation(self, parent_id, child_id, rel_type_name):
        rel_type = self.taskrelationtype_set.get(name__exact=rel_type_name)
        parent = self.task_set.get(identifier__exact=parent_id)
        child = self.task_set.get(identifier__exact=child_id)
        TaskRelation.objects.create(project=self, from_task=parent, to_task=child, type=rel_type)

    def _create_task(self, regular_fields, additional_fields):

        regular_fields['milestone'] = self._register_regular(regular_fields.get('milestone'), Milestone)
        regular_fields['assignee'] = self._register_regular(regular_fields.get('assignee'), Assignee)
        regular_fields['category'] = self._register_regular(regular_fields.get('category'), TaskCategory)
        regular_fields['state'] = self._register_regular(regular_fields.get('state'), TaskState)

        new_task = Task.objects.create(project=self, **regular_fields)

        additional_fields = additional_fields or [{}]
        for kwargs in additional_fields:
            if kwargs:
                TaskAdditionalField.objects.create(project=self, task=new_task, **kwargs)

        return new_task

    def _register_regular(self, value, field_type):
        if value:
            requested = field_type.objects.filter(project=self, name__exact=value)
            if requested.count() == 1:
                return requested[0]
            else:
                return field_type.objects.create(project=self, name=value, active=False)
        else:
            return field_type.objects.get_or_create(project=self, name='__NONE')[0]


class ProjectRelation(models.Model):

    class Meta:
        unique_together = ('parent', 'child')

    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
    parent = models.ForeignKey(Project, related_name='parent', on_delete=models.CASCADE)
    child = models.ForeignKey(Project, related_name='child', on_delete=models.CASCADE)


class Milestone(models.Model):

    class Meta:
        unique_together = ('project', 'name')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='__NONE')
    date = models.DateField(default=date(year=1, month=1, day=1))
    active = models.BooleanField(default=True)


class Assignee(models.Model):

    class Meta:
        unique_together = ('project', 'name')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskCategory(models.Model):

    class Meta:
        unique_together = ('project', 'name')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskState(models.Model):

    class Meta:
        unique_together = ('project', 'name')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskRelationType(models.Model):

    class Meta:
        unique_together = ('project', 'name')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class Task(models.Model):

    class Meta:
        unique_together = ('project', 'identifier')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    identifier = models.IntegerField()
    assignee = models.ForeignKey(Assignee)
    milestone = models.ForeignKey(Milestone)
    category = models.ForeignKey(TaskCategory)
    state = models.ForeignKey(TaskState)

    def __str__(self):
        return 'pid:{} id:{} {} {} {} {}'.format(self.project.identifier, self.identifier, self.assignee,
                                                 self.milestone, self.category, self.state)


class TaskAdditionalField(models.Model):

    type_choices = ((0, 'CharField'), (1, 'TextField'), (2, 'DateField'))

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=type_choices)
    char = models.CharField(max_length=255, default='')
    text = models.TextField(default='')
    date = models.DateField(default=date(year=1, month=1, day=1))


class TaskRelation(models.Model):

    class Meta:
        unique_together = ('from_task', 'to_task', 'type')

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    from_task = models.ForeignKey(Task)
    to_task = models.ForeignKey(Task)
    type = models.ForeignKey(TaskRelationType)
