import uuid

import django
import inflect
from django.db import models
from django.utils import timezone

if django.VERSION < (4, 0):
    from django.utils.translation import ugettext_lazy as _
else:
    from django.utils.translation import gettext_lazy as _

from django.utils.translation import trans_real

from django_insights.choices import BucketType
from django_insights.database import database_entry
from django_insights.managers import BucketManager

# FIXME: rename to something sane!
p = inflect.engine()


def custom_gettext(msg):
    # Should be a better method?
    return trans_real._default._catalog.get(msg)  # noqa


class App(models.Model):
    """Apps that have insights"""

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    name = models.CharField(max_length=254, db_index=True, unique=True)

    def translated_name(self) -> str:
        # FIXME: this sucks bigtome
        names = self.name.split(".")
        names.pop()
        name = names.pop()

        if custom_gettext(name) is None:
            print("name", p.singular_noun(name))
            if p.singular_noun(name):
                return _(f"{p.singular_noun(name)}").title()
            else:
                return name.title()

        return _(f"{name}").title()


class ExecutionDelta(models.Model):
    """Delta is stored on every run and used for filtering, these values should never change"""

    executed_at = models.DateTimeField(db_index=True, default=timezone.now)
    uuid = models.UUIDField(default=uuid.uuid4)


class MetricModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    label = models.CharField(max_length=254, db_index=True, unique=True)

    question = models.TextField(blank=True, null=True)
    desc = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True


class Counter(MetricModel):
    """Simple counter, can incr or decr, label and app are unique"""

    value = models.IntegerField(default=0)
    app = models.ForeignKey(App, related_name='counters', on_delete=models.CASCADE)

    class Meta:
        app_label = database_entry
        constraints = [
            models.UniqueConstraint(
                fields=['app', 'label'], name='counter_unique_app_label'
            )
        ]

    def __str__(self):
        return f"Insight Counter: {self.label} = {self.value}"


class Gauge(MetricModel):
    """Simple gauge, can be set or set with delta, label and app are unique"""

    value = models.FloatField(default=float(0.0))
    app = models.ForeignKey(App, related_name='gauges', on_delete=models.CASCADE)

    def gauge(self, value=1, delta=False) -> int:
        """Set gauge value"""
        if not delta:
            self.value = value
        else:
            self.value = self.value + value

    class Meta:
        app_label = database_entry
        constraints = [
            models.UniqueConstraint(
                fields=['app', 'label'], name='gauge_unique_app_label'
            )
        ]

    def __str__(self):
        return f"Insight Gauge: {self.label} = {self.value}"


class Bucket(MetricModel):
    app = models.ForeignKey(App, related_name='buckets', on_delete=models.CASCADE)

    type = models.IntegerField(
        choices=BucketType.BUCKET_TYPES, default=BucketType.TIME_SERIES
    )

    # Bucket specific plot options
    xlabel = models.CharField(max_length=254, blank=True, null=True)
    xformat = models.CharField(max_length=254, blank=True, null=True)
    ylabel = models.CharField(max_length=254, blank=True, null=True)
    yformat = models.CharField(max_length=254, blank=True, null=True)

    # title for plot
    title = models.CharField(max_length=254, blank=True, null=True)

    @property
    def is_timeseries(self) -> bool:
        return self.type == BucketType.TIME_SERIES

    @property
    def is_histogram(self) -> bool:
        return self.type == BucketType.HISTOGRAM

    @property
    def is_scatterplot(self) -> bool:
        return self.type == BucketType.SCATTERPLOT

    objects = BucketManager()

    class Meta:
        app_label = database_entry
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'app',
                    'label',
                ],
                name='bucket_unique_app_label_timestamp',
            )
        ]


class BucketValue(models.Model):
    """
    Simple bucket value map, used for time-series, histogram and scatterpltos,
    timestamp, label and app are unique together
    """

    # Timestamp for timeseries
    timestamp = models.DateTimeField(db_index=True, blank=True, null=True)

    # Matrix
    xvalue = models.FloatField(default=float(0.0))
    yvalue = models.FloatField(default=float(0.0))
    category = models.CharField(db_index=True, max_length=254, null=True)

    bucket = models.ForeignKey(Bucket, related_name='values', on_delete=models.CASCADE)

    class Meta:
        app_label = database_entry
        constraints = [
            models.UniqueConstraint(
                fields=['bucket', 'timestamp'],
                name='bucketvalue_unique_bucket_timestamp',
            )
        ]

    def __str__(self):
        return (
            "Insight Bucket value: "
            f" timestamp={self.bucket.label}.{self.timestamp} x={self.xvalue} y={self.yvalue}"
        )
