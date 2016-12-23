from taskgraph.tasktracker.abstract import Action
from taskgraph.tasktracker.abstract import Task as AbstractTask

from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField

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
        unique_together = ('url', 'type',)

    url = models.CharField(max_length=255)
    type = ChoicesHelper.char_field_with_choices(Supported)
    user_name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    projects = ListField(EmbeddedModelField('Project'))
    projects_relations = ListField(EmbeddedModelField('ProjectRelation'))
    task_colors = ListField(EmbeddedModelField('TaskColor'))


    def __str__(self):
        return '{} {}'.format(self.url, self.type)

    def has_project_list(self):
        return len(self.projects) > 0

    def restore_project_list(self, i_tracker):
        with i_tracker.connect(self) as interface:
            for deprecated_project in self.projects:
                deprecated_project.delete()

            while len(self.projects): self.projects.pop()

            project_list = interface.get_projects()

            new_projects_lst = []
            for new_project in project_list:
                project_model = Project(tracker=self, identifier=new_project.identifier,
                                        name=new_project.name, description=new_project.description)
                self.projects.append(project_model)
                project_model.restore_meta(new_project)
                new_projects_lst.append((project_model, new_project))

            for model, project in new_projects_lst:
                model.restore_children(project, self)
                model.save()

            while len(self.projects_relations): self.projects_relations.pop()

            self.save()

    def update_projects_if_not_created(self, i_tracker):
        if not self.has_project_list():
            self.restore_project_list(i_tracker)

    def has_tasks(self):
        active = self.project_set.filter(is_active__exact=True)
        for project in active:
            if project.task_set.all().count() == 0:
                return False
        return True

    def restore_project_tasks(self, i_tracker, only_active=True):
        if only_active:
            active_project_list = filter(lambda p: p.is_active, self.projects)
            if not active_project_list:
                return
        else:
            active_project_list = self.projects

        with i_tracker.connect(self) as interface:
            for project in active_project_list:
                project.restore_project_tasks(interface)

    def update_task_if_not_created(self, i_tracker):
        if not self.has_tasks():
            self.restore_project_tasks(i_tracker)


class Project(models.Model):

    class Meta:
        unique_together = ('identifier',)

    tracker = models.ForeignKey(Tracker)
    identifier = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=False)

    tasks = ListField(EmbeddedModelField('Task'))
    tasks_relations = ListField(EmbeddedModelField('TaskRelation'))
    task_relation_types = ListField(EmbeddedModelField('TaskRelationType'))

    assignees = ListField(EmbeddedModelField('Assignee'))
    milestones = ListField(EmbeddedModelField('Milestone'))
    task_categories = ListField(EmbeddedModelField('TaskCategory'))
    task_states = ListField(EmbeddedModelField('TaskState'))

    def is_member(self, name):
        return len(filter(lambda a: a.name == name, self.assignees)) == 1

    def restore_meta(self, project_from_tracker):
        self._restore_meta(Milestone, project_from_tracker.meta.milestones, self.milestones)
        self._restore_meta(Assignee, project_from_tracker.meta.assignees, self.assignees)
        self._restore_meta(TaskCategory, project_from_tracker.meta.task_categories, self.task_categories)
        self._restore_meta(TaskState, project_from_tracker.meta.task_states, self.task_states)
        self._restore_meta(TaskRelationType, project_from_tracker.meta.relation_types, self.task_relation_types)
        self.save()

    def restore_children(self, project_from_tracker, tracker):
        current_children = self.get_child_list(tracker)

        for deprecated in current_children:
            deprecated.delete()

        if not project_from_tracker.child_id_list:
            return

        for child_id in project_from_tracker.child_id_list:
            child_model = filter(lambda p: p.identifier == child_id, tracker.projects)[0]
            tracker.projects_relations.append(ProjectRelation(parent=self, child=child_model))

    def get_child_list(self, tracker):
        return [relation.child for relation in
                filter(lambda p: p.parent.identifier == self.identifier, tracker.projects_relations)]

    def restore_project_tasks(self, i_tracker):
        for task in self.tasks:
            task.delete()

        while len(self.tasks) > 0: self.tasks.pop()

        tasks = i_tracker.get_tasks(self.identifier)
        for task, additional, task_children in tasks:
            self._create_task(task.regular_fields_as_dict(), additional).save()

        for rel in self.tasks_relations:
            rel.delete()

        for task, _, task_children in tasks:
            for child_id, rel_type in task_children or []:
                try:
                    self._create_relation(task.identifier, child_id, rel_type).save()
                except IndexError:
                    print 'can\'t create relation from %i to %i  with type %s' \
                          % (task.identifier, child_id, rel_type)

        self.save()

    @staticmethod
    def _restore_meta(cls_model, new_model_data, old_model_set):
        if not new_model_data:
            return

        for deprecated_model in old_model_set:
            deprecated_model.delete()

        while len(old_model_set) > 0: old_model_set.pop()

        for new_model in new_model_data:
            if new_model:
                old_model_set.append(cls_model.objects.create(**new_model))

    def _create_relation(self, parent_id, child_id, rel_type_name):
        def get(predicate, collection):
            fltr = filter(predicate, collection)
            if not fltr or len(fltr) > 1:
                raise IndexError
            return fltr[0]

        rel_type = get(lambda rt: rt.name == rel_type_name, self.task_relation_types)
        parent = get(lambda t: t.identifier == parent_id, self.tasks)
        child = get(lambda t: t.identifier == child_id, self.tasks)

        tr = TaskRelation(project=self, from_task=parent, to_task=child, type=rel_type)
        return tr

    def _create_task(self, reg_fields, additional_fields):

        reg_fields['project'] = self
        reg_fields['milestone'] = self._register_regular(reg_fields.get('milestone'), Milestone, self.milestones)
        reg_fields['assignee'] = self._register_regular(reg_fields.get('assignee'), Assignee, self.assignees)
        reg_fields['category'] = self._register_regular(reg_fields.get('category'), TaskCategory, self.task_categories)
        reg_fields['state'] = self._register_regular(reg_fields.get('state'), TaskState, self.task_states)

        new_task = Task(**reg_fields)

        additional_fields = additional_fields or [{}]
        for kwargs in additional_fields:
            if kwargs:
                new_task.additional_field.append(TaskAdditionalField.objects.create(**kwargs))

        return new_task

    @staticmethod
    def _register_regular(value, field_type, field_set):
        if value:
            requested = filter(lambda f: f.name == value['name'], field_set)
            if len(requested) == 1:
                return requested[0]
            else:
                value['active'] = False
                new_f = field_type.objects.create(**value)
                field_set.append(new_f)
                return new_f
        else:
            requested = filter(lambda f: f.name == '__NONE', field_set)
            if len(requested) == 1:
                return requested[0]
            else:
                new_f = field_type.objects.create(name='__NONE', identifier=1, active=False)
                field_set.append(new_f)
                return new_f


class ProjectRelation(models.Model):

    parent = models.ForeignKey(Project, related_name='parent')
    child = models.ForeignKey(Project, related_name='child')


class Milestone(models.Model):

    identifier = models.IntegerField(default=1)
    name = models.CharField(max_length=255, default='__NONE')
    date = models.DateField(default=date(year=1, month=1, day=1))
    active = models.BooleanField(default=True)


class Assignee(models.Model):

    class Meta:
        unique_together = ('identifier',)

    identifier = models.IntegerField()
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskCategory(models.Model):

    identifier = models.IntegerField()
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskState(models.Model):

    identifier = models.IntegerField()
    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class TaskRelationType(models.Model):

    name = models.CharField(max_length=255, default='__NONE')
    active = models.BooleanField(default=True)


class Task(models.Model):

    project = models.ForeignKey(Project)
    identifier = models.IntegerField()
    assignee = models.ForeignKey(Assignee)
    milestone = models.ForeignKey(Milestone)
    category = models.ForeignKey(TaskCategory)
    state = models.ForeignKey(TaskState)

    additional_field = ListField(EmbeddedModelField('TaskAdditionalField'))

    def __str__(self):
        return 'id:{} {} {} {} {}'.format(self.identifier, self.assignee,
                                          self.milestone, self.category, self.state)

    def to_abstract(self, project_id):
        abstract_task = AbstractTask()
        abstract_task.identifier = self.identifier
        abstract_task.project_identifier = project_id

        if self.assignee.name != '__NONE':
            abstract_task.assignee = self.assignee.identifier
        if self.milestone.name != '__NONE':
            abstract_task.milestone = (self.milestone.name, self.milestone.date)
        if self.category.name != '__NONE':
            abstract_task.category = self.category.identifier
        if self.state.name != '__NONE':
            abstract_task.status = self.state.identifier

        for add_field in self.additional_field:
            if add_field.type == 'CharField':
                abstract_task.add_char_field(add_field.name, add_field.char)
            elif add_field.type == 'TextField':
                abstract_task.add_text_field(add_field.name, add_field.text)
            elif add_field.type == 'DateField':
                abstract_task.add_date_field(add_field.name, add_field.date)

        return abstract_task

    def delete(self, i_tracker=None, using=None):
        if i_tracker:
            i_tracker.update_task(Action(self.to_abstract(self.project.identifier), Action.Type.DELETE))
        self.project.tasks.remove(self)
        models.Model.delete(self, using=using)

    def save(self, save_on_tracker=False, create_on_tracker=False, i_tracker=None,
             force_insert=False, force_update=False, using=None, update_fields=None):
        assert not save_on_tracker or not create_on_tracker
        try:
            self.project.tasks.remove(self)
        except ValueError:
            pass
        self.project.tasks.append(self)
        models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using,
                          update_fields=update_fields)

        if not save_on_tracker and not create_on_tracker:
            return

        act_type = save_on_tracker and Action.Type.CHANGE or create_on_tracker and Action.Type.CREATE

        assert i_tracker
        i_tracker.update_task(Action(self.to_abstract(self.project.identifier), act_type))


class TaskAdditionalField(models.Model):

    type_choices = ((0, 'CharField'), (1, 'TextField'), (2, 'DateField'))

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=type_choices)
    char = models.CharField(max_length=255, default='')
    text = models.TextField(default='')
    date = models.DateField(default=date(year=1, month=1, day=1))


class TaskRelation(models.Model):

    class Meta:
        unique_together = ('from_task', 'to_task', 'type')

    project = models.ForeignKey(Project)
    from_task = models.ForeignKey(Task)
    to_task = models.ForeignKey(Task)
    type = models.ForeignKey(TaskRelationType)

    def delete(self, i_tracker=None, using=None):
        if i_tracker:
            i_tracker.update_relation(Action(self, Action.Type.DELETE))
        self.project.tasks_relations.remove(self)
        models.Model.delete(self, using=using)

    def save(self, i_tracker=None, force_insert=False, force_update=False, using=None, update_fields=None):
        if i_tracker:
            i_tracker.update_relation(Action(self, Action.Type.CREATE))
        try:
            self.project.tasks_relations.remove(self)
        except ValueError:
            pass
        self.project.tasks_relations.append(self)
        models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using,
                          update_fields=update_fields)


class TaskColor(models.Model):

    task_identifier = models.IntegerField()
    color = models.IntegerField()

