from django.http import HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse

from .serializers import LogSerializer

from .models import Log
from . import urls
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.shortcuts import render

# Create your views here.
class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


def LogViewerHomePage(request):
    logs = Log.objects.all().order_by('-timestamp')
    args = {}
    args['logs'] = logs
    return TemplateResponse(request, "listing.html", args)

def LogVewerRequest(request):
