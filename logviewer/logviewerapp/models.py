from email.policy import default
import uuid
from django.forms import JSONField
from djongo import models
from django.utils.translation import gettext_lazy as _
from numpy import require

from .fields import MyJSONField

# Create your models here.
class Log(models.Model):
    class Severity(models.TextChoices):
        LOW = 'L', _('Low')
        MODERATE = 'M', _('Moderate')
        HIGH = 'H', _('High')
        CRITICAL = 'C', _('Critical')

    class Type(models.TextChoices):
        INFO = 'I', _('Info')
        ERROR = 'E', _('Error')
        WARNING = 'W', _('Warning')
        SUCCESS = 'S', _('Success')
        RECOMMENDATION = 'R', _('Recommendation')

    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=100)
    timestamp = models.TimeField()
    severity = models.CharField(
        max_length=1,
        choices=Severity.choices,
        default=Severity.LOW
    )
    type = models.CharField(
        max_length=1,
        choices=Type.choices,
        default=Type.INFO
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    error = MyJSONField("error", default={}, blank=True)
    details = MyJSONField("details", default={}, blank=True)
