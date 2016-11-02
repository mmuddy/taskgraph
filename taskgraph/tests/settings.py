from taskgraph.model.model import Tracker

# tracker = None


def tracker_dummy():
    return Tracker.objects.get_or_create(url='no-validation', user_name='no-validation',
                                         password='no-validation', type='Dummy')[0]


def tracker_redmine():
    return Tracker.objects.get_or_create(url='https://dev.osll.ru/', user_name='yakovlevvladyakovlev@yandex.ru',
                                         password='1q2w3e4r', type='Redmine')[0]