from taskgraph.model import model
from . import alertfactory

from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import render

from copy import copy


def trackers_alert(func, *args):
    return func(*args, css_container_class='col-sm-9 col-sm-offset-3 col-md-10 col-md-offset-2')


def profile_page(request):
    return trackers_page(request)


def trackers_page(request):
    return trackers_list_page(request)


class TrackersSubMenu:

    class Item:
        def __init__(self, name, url, active=False):
            self.url = url
            self.name = name
            self.css_class = ''
            self.active = active
            self.set_active(active)

        def set_active(self, active=True):
            self.active = active
            if active:
                self.css_class = 'class="active"'

        def as_active(self):
            new = copy(self)
            new.set_active()
            return new

    List = Item('List', 'trackers-list')
    Add = Item('Add', 'trackers-add')
    Edit = Item('Edit', '')

    @staticmethod
    def for_tracker():
        return [TrackersSubMenu.List,
                TrackersSubMenu.Add]

    @staticmethod
    def for_list():
        return [TrackersSubMenu.List.as_active(),
                TrackersSubMenu.Add]

    @staticmethod
    def for_add():
        return [TrackersSubMenu.List,
                TrackersSubMenu.Add.as_active()]

    @staticmethod
    def for_edit():
        return [TrackersSubMenu.List,
                TrackersSubMenu.Add,
                TrackersSubMenu.Edit.as_active()]


def trackers_list_page(request, alerts=None):
    trackers = model.Tracker.objects.order_by('type', 'url', 'user_name')

    for tracker in trackers:
        tracker.hash = hash(tracker)
        print(tracker.hash)

    context = {'is_user_active': True,
               'contains_menu': True,
               'sub_menu': TrackersSubMenu.for_list(),
               'tracker_list': trackers,
               'alerts': alerts}

    return render(request, 'taskgraph/profile/trackers_list.html', context)


def trackers_add_page(request):

    context = {'is_user_active': True,
               'contains_menu': True,
               'sub_menu': TrackersSubMenu.for_add()}

    if request.method == 'POST':
        return trackers_add_page_post(request, context)

    return render(request, 'taskgraph/profile/trackers_add.html', context)


def trackers_add_page_post(request, context):
    url = ''
    login = ''
    password = ''
    tracker_type = 'Redmine'

    try:
        url = request.POST['url']
        login = request.POST['login']
        password = request.POST['password']
    except KeyError:
        context['alerts'] = [trackers_alert(alertfactory.error, 'Not all required data field')]
        return render(request, 'taskgraph/profile/trackers_add.html', context)
    finally:
        context['tracker_url'] = url
        context['tracker_login'] = login
        context['tracker_password'] = password

    try:
        model.Tracker.objects.create(url=url, user_name=login, password=password, type=tracker_type)
    except IntegrityError:
        context['alerts'] = [trackers_alert(alertfactory.error, 'Posted data isn\'t unique')]
        return render(request, 'taskgraph/profile/trackers_add.html', context)

    return trackers_list_page(request, alerts=[trackers_alert(alertfactory.success,
                                                              'Changes in tracker list was applied')])


def trackers_edit_page(request, tracker_hash):
    requested_tracker = None
    print(tracker_hash)
    for tracker in model.Tracker.objects.all():
        print(hash(tracker))
        print(hash(tracker) == int(tracker_hash))
        if hash(tracker) == int(tracker_hash):
            requested_tracker = tracker

    if not requested_tracker:
        raise Http404('No Tracker matches the given query.')

    context = {'is_user_active': True,
               'contains_menu': True,
               'tracker_url': requested_tracker.url,
               'tracker_login': requested_tracker.user_name,
               'tracker_hash': hash(requested_tracker),
               'sub_menu': TrackersSubMenu.for_edit()}

    if request.method == 'POST':
        return trackers_edit_page_post(request, context, requested_tracker)

    return render(request, 'taskgraph/profile/trackers_edit.html', context)


def trackers_edit_page_post(request, context, tracker):
    try:
        url = request.POST['url']
        login = request.POST['login']
        password = request.POST['password']
    except KeyError:
        context['alerts'] = [trackers_alert(alertfactory.error, 'Not all required data field')]
        return render(request, 'taskgraph/profile/trackers_edit.html', context)

    try:
        tracker.url = url
        tracker.user_name = login
        tracker.password = password
        tracker.save()
    except IntegrityError:
        context['alerts'] = [trackers_alert(alertfactory.error, 'Posted data isn\'t unique')]
        return render(request, 'taskgraph/profile/trackers_edit.html', context)

    return trackers_list_page(request, alerts=[trackers_alert(alertfactory.success,
                                                              'Changes in tracker list was applied')])


def trackers_delete(request, tracker_hash):
    print(tracker_hash)
    requested_tracker = None
    for tracker in model.Tracker.objects.all():
        print('{} hash:{}'.format(repr(tracker), hash(tracker)))
        if hash(tracker) == int(tracker_hash):
            requested_tracker = tracker

    if not requested_tracker:
        raise Http404('No Tracker matches the given query.')

    requested_tracker.delete()

    return trackers_list_page(request, alerts=[trackers_alert(alertfactory.success, 'Tracker has been deleted')])
