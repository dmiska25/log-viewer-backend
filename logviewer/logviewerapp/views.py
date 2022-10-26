from django.http import HttpResponse
from django.shortcuts import render

from .serializers import LogSerializer

from .models import Log
from . import urls
from rest_framework import viewsets
from rest_framework import permissions

# Create your views here.
class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]
