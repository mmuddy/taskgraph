from django.db import models


class TrackerConnectionInf(models.Model):

    SUPPORTED_TRACKERS = (('RM', 'Redmine'),)

    # tracker_type = models.CharField(max_length=1, choices=SUPPORTED_TRACKERS)
    # url_to_connect = models.URLField()

    # login = models.CharField()
    # password = models.CharField()
