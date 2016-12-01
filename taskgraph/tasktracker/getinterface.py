from taskgraph.tests.trackerdummy import TrackerDummy
from taskgraph.tasktracker.iredmine import IRedmine

tracker_map = {'Dummy': TrackerDummy(),
               'Redmine': IRedmine()}


def get_interface(tracker_type):
    return tracker_map[tracker_type]