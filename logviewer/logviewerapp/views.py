from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.template.response import TemplateResponse

from .serializers import LogSerializer

from .models import Log
from . import urls
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.shortcuts import render
from datetime import datetime
from django.core.paginator import Paginator

PAGINATION_LIMIT = 30

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

def listing(request):
    time_before = datetime.fromisoformat(request.GET.get('time_before', datetime.now().isoformat()))
    page = int(request.GET.get('page', 1))
    logs = Log.objects.all().order_by('-timestamp').filter(timestamp__lt=time_before)
    paginator = Paginator(logs, PAGINATION_LIMIT)
    page_response = paginator.get_page(page)
    
    args = {}
    args['component'] = "listing"
    args['logs'] = page_response
    args['load_more_link'] = f"?time_before={time_before.isoformat()}&page={page+1}"
    args['page'] = page
    
    if request.htmx:
        if page > 1:
            return TemplateResponse(request, "listing/listing_results.html", args)
        return TemplateResponse(request, "listing/listing.html", args)
    return TemplateResponse(request, "homepage.html", args)

def details(request, id):
    log = Log.objects.get(_id = id)
    
    args = {}
    args['log'] = log

    return TemplateResponse(request, "listing/log_details.html", args)


