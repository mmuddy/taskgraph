from taskgraph.model.model import Tracker

# tracker = None


def tracker_dummy():
    dummies = Tracker.objects.filter(url='no-validation', type='Dummy',
                                     user_name='yakovlevvladyakovlev@yandex.ru', password='1q2w3e4r')
    if dummies:
        return dummies[0]
    else:
        dummy = Tracker.objects.create(url='no-validation', type='Dummy',
                                       user_name='yakovlevvladyakovlev@yandex.ru', password='1q2w3e4r')
        return dummy


def tracker_redmine():
    dummies = Tracker.objects.filter(url='https://dev.osll.ru/', type='Redmine',
                                     user_name='yakovlevvladyakovlev@yandex.ru', password='1q2w3e4r')
    if dummies:
        return dummies[0]
    else:
        dummy = Tracker.objects.create(url='https://dev.osll.ru/', type='Redmine',
                                       user_name='yakovlevvladyakovlev@yandex.ru', password='1q2w3e4r')
        return dummy
