from collections import OrderedDict
from datetime import datetime
import pprint

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.template.response import TemplateResponse
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .rawQuery import aggregate

from . import urls
from .fusioncharts import FusionCharts
from .models import Log
from .serializers import LogSerializer

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
    search = request.GET.get('search', None)
    page = int(request.GET.get('page', 1))

    logs = Log.objects.all().order_by('-timestamp').filter(timestamp__lt=time_before)
    if search != None:
        logs = logs.filter(title__contains=search)
    paginator = Paginator(logs, PAGINATION_LIMIT)
    page_response = paginator.get_page(page)
    
    args = {}
    args['component'] = "listing"
    args['logs'] = page_response
    args['load_more_link'] = f"?time_before={time_before.isoformat()}&page={page+1}&search={search or ''}"
    args['page'] = page
    args['search'] = search
    
    if request.htmx:
        if page > 1 or search != None:
            return TemplateResponse(request, "listing/listing_results.html", args)
        return TemplateResponse(request, "listing/listing.html", args)
    return TemplateResponse(request, "homepage.html", args)

def details(request, id):

    if not request.htmx:
        return HttpResponseNotFound()

    args = {}
    args['log'] = Log.objects.get(_id = id)

    return TemplateResponse(request, "listing/log_details.html", args)

def exceptions(request):
    args = {}
    args['component'] = "exceptions"
    args['top_exceptions'] = getTopExceptionsGraph(request)
    args['timeline'] = getExceptionTimelineGraph(request)

    if request.htmx:
        return TemplateResponse(request, "exceptions/exceptions.html", args)
    return TemplateResponse(request, "homepage.html", args)

def topExceptions(request):

    return

def timeline(request):

    return




# Helpers
def getTopExceptionsGraph(request):

    return

def getExceptionTimelineGraph(request):
    # TODO: will also need to where statement for newest and type, order, and update unit/binSize accordingly
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp", "unit": "day", "binSize": 1,
                    }
                },
                "count": {"$sum": 1}
            }
        }
    ]
    dates = aggregate(pipeline)

    dataSource = OrderedDict()
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Countries With Most Oil Reserves [2017-18]"
    chartConfig["subCaption"] = "In MMbbl = One Million barrels"
    chartConfig["xAxisName"] = "Country"
    chartConfig["yAxisName"] = "Reserves (MMbbl)"
    chartConfig["theme"] = "fusion"

    dataSource["chart"] = chartConfig

    dataSource['data'] = []
    for date in dates:
        dataSource['data'].append(
            {
                "label": date['_id'].strftime("%m/%d/%Y, %H:%M:%S"), 
                "value": date['count']
            }
        )

    return FusionCharts("column2d", "myFirstChart", "600", "400", "myFirstchart-container", "json", dataSource).render()