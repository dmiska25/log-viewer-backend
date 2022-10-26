from rest_framework import serializers
from .models import Log

class LogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Log
        fields = ['url', 'service_name', 'timestamp', 'severity', 'type', 'title', 'description', 'error', 'details']
