from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.paginator import Paginator
from django.shortcuts import render
from django.template.response import TemplateResponse
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from django.core.exceptions import SuspiciousOperation

from .rawQuery import aggregate

from .fusioncharts import FusionCharts
from .models import Log
from .serializers import LogSerializer

PAGINATION_LIMIT = 30
QUERY_FIELDS = [
    "service_name",
    "severity",
    "title",
]

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
        raise SuspiciousOperation('Invalid JSON')

    args = {}
    args['log'] = Log.objects.get(_id = id)

    return TemplateResponse(request, "listing/log_details.html", args)

def exceptionCategories(request):
    args = {}
    args['component'] = "exceptions"
    args['top_exceptions'] = getTopExceptionsGraph(request)
    args['timeline'] = getExceptionTimelineGraph(request)
    args['fields'] = QUERY_FIELDS

    if request.htmx:
        return TemplateResponse(request, "exceptions/exceptions.html", args)
    return TemplateResponse(request, "homepage.html", args)

def topExceptions(request):
    args = {}
    args['top_exceptions'] = getTopExceptionsGraph(request)
    args['fields'] = QUERY_FIELDS
    return TemplateResponse(request, "exceptions/top_exceptions.html", args)

def timeline(request):
    args = {}
    args['timeline'] = getExceptionTimelineGraph(request)
    return TemplateResponse(request, "exceptions/timeline.html", args)

def userInformation(request):
    args = {}
    args['component'] = "users"
    args['user_sessions'] = getUserActivityGraph(request)
    args['users'] = getUsersGraph(request)

    if request.htmx:
        return TemplateResponse(request, "users/users.html", args)
    return TemplateResponse(request, "homepage.html", args)

def userDuration(request):
    args = {}
    args['user_sessions'] = getUserActivityGraph(request)
    return  TemplateResponse(request, "users/user_sessions.html", args)

def users(request):
    args = {}
    args['users'] = getUsersGraph(request)
    return  TemplateResponse(request, "users/users_per_period.html", args)

# Graph Queries ===============================================================
def getTopExceptionsGraph(request):
    field = request.GET.get('field', "severity")
    if not QUERY_FIELDS.__contains__(field):
        raise SuspiciousOperation('Invalid Field')

    pipeline = [
        {
            "$match": {
                "type": "E",
            }
        },
        {
            "$group": {
                "_id": f"${field}",
                "count": {"$sum": 1}
            }
        },
        {
            "$limit": 5
        },
        {
            "$sort": {"count": -1}
        },
    ]

    exceptionCategories = list(aggregate(pipeline))

    dataSource = OrderedDict()
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Top Errors"
    chartConfig["subCaption"] = f"by {field}"
    chartConfig["xAxisName"] = f"{field}"
    chartConfig["yAxisName"] = "Errors"
    chartConfig["theme"] = "fusion"

    dataSource["chart"] = chartConfig

    dataSource['data'] = []
    for exceptionCategory in exceptionCategories:
        dataSource['data'].append(
            {
                "label": exceptionCategory['_id'], 
                "value": exceptionCategory['count']
            }
        )

    return FusionCharts("bar2d", f"top-exceptions-{datetime.now().strftime('%H/%M/%S')}", "1000", "400", "top-exceptions-wrapper", "json", dataSource).render()


display = {
    "daily": {
        "start": (datetime.today() - timedelta(days=59)).replace(hour=0, minute=0, second=0, microsecond=0),
        "datetrunc": {
                    "date": "$timestamp", "unit": "day", "binSize": 1,
        }
    },
    "hourly": {
        "start": (datetime.now() - timedelta(hours=59)).replace(minute=0, second=0, microsecond=0),
        "datetrunc": {
                    "date": "$timestamp", "unit": "hour", "binSize": 1,
        }
    },
    "5-minute": {
        "start": (datetime.now() - timedelta(minutes=59*5)).replace(minute=(datetime.now().minute//5 * 5), second=0, microsecond=0),
        "datetrunc": {
                    "date": "$timestamp", "unit": "minute", "binSize": 5,
        }
    }
}

def getExceptionTimelineGraph(request):
    increment = request.GET.get('increment', "hourly")

    pipeline = [
        {
            "$match": {
                "type": "E",
                "timestamp": {"$gt": display[increment]["start"] }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateTrunc": display[increment]["datetrunc"]
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    timestamps = list(aggregate(pipeline))
    timestamp_range = getTimestampArray(display[increment]["start"], increment, 59)
    timeline = [{**u, **v} for u, v in sortedZipLongest(timestamp_range, timestamps, key="_id", fillvalue={})]

    dataSource = OrderedDict()
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Errors over time"
    chartConfig["subCaption"] = f"{increment} Increments"
    chartConfig["xAxisName"] = "Time"
    chartConfig["yAxisName"] = "Errors"
    chartConfig["theme"] = "fusion"
    chartConfig["labelStep"] = "1"
    chartConfig["labelFontSize"] = "10"
    chartConfig["slantLabel"] = "1"

    dataSource["chart"] = chartConfig

    dataSource['data'] = []
    for timestamp in timeline:
        dataSource['data'].append(
            {
                "label": timestamp['_id'].strftime("%m/%d/%Y, %H:%M:%S") if \
                    timestamp['_id'].hour == 0 and timestamp['_id'].minute == 0 and\
                    timestamp['_id'].second == 0 else timestamp['_id'].strftime("%H:%M:%S"), 
                "value": timestamp['count']
            }
        )

    return FusionCharts("column2d", f"exceptions-timeline-{datetime.now().strftime('%H/%M/%S')}", "1000", "400", "exceptions-timeline-wrapper", "json", dataSource).render()

def getUserActivityGraph(request):
    increment = request.GET.get('increment', "hourly")

    pipeline = [
        {
            "$match": {
                "type": "I",
                "service_name": "user device",
                "details.notice": {"$in": ["logon", "logoff"]},
                "timestamp": {"$gt": display[increment]["start"] },
            }
        },
        {
            "$group": {
                "_id": "$details.session_id",
                "timestamp": { "$min": "$timestamp" },
                "session_end": { "$max": "$timestamp" },
            },
        },
        {
            "$group": {
                "_id": {
                    "$dateTrunc": display[increment]["datetrunc"]
                },
                "count": {"$avg": {"$divide": [{"$subtract": ["$session_end", "$timestamp"]}, 60000]}}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    timestamps = list(aggregate(pipeline))
    timestamp_range = getTimestampArray(display[increment]["start"], increment, 59)
    timeline = [{**u, **v} for u, v in sortedZipLongest(timestamp_range, timestamps, key="_id", fillvalue={})]

    dataSource = OrderedDict()
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Average User Session Time"
    chartConfig["subCaption"] = f"{increment} Increments"
    chartConfig["xAxisName"] = "Time"
    chartConfig["yAxisName"] = "Duration (minutes)"
    chartConfig["theme"] = "fusion"
    chartConfig["labelStep"] = "1"
    chartConfig["labelFontSize"] = "10"
    chartConfig["slantLabel"] = "1"

    dataSource["chart"] = chartConfig

    dataSource['data'] = []
    for timestamp in timeline:
        dataSource['data'].append(
            {
                "label": timestamp['_id'].strftime("%m/%d/%Y, %H:%M:%S") if \
                    timestamp['_id'].hour == 0 and timestamp['_id'].minute == 0 and\
                    timestamp['_id'].second == 0 else timestamp['_id'].strftime("%H:%M:%S"), 
                "value": timestamp['count']
            }
        )

    return FusionCharts("column2d", f"user-sessions-timeline-{datetime.now().strftime('%H/%M/%S')}", "1000", "400", "user-sessions-timeline-wrapper", "json", dataSource).render()


def getUsersGraph(request):
    increment = request.GET.get('increment', "hourly")

    pipeline = [
        {
            "$match": {
                "type": "I",
                "service_name": "user device",
                "details.notice": "logon",
                "timestamp": {"$gt": display[increment]["start"] },
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateTrunc": display[increment]["datetrunc"]
                },
                "users": {"$addToSet": "$details.user_id"}
            }
        },
        {
            "$project": {
                "_id": "$_id",
                "count": { "$size": "$users" }
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    timestamps = list(aggregate(pipeline))
    timestamp_range = getTimestampArray(display[increment]["start"], increment, 59)
    timeline = [{**u, **v} for u, v in sortedZipLongest(timestamp_range, timestamps, key="_id", fillvalue={})]

    dataSource = OrderedDict()
    chartConfig = OrderedDict()
    chartConfig["caption"] = "Users Per Period"
    chartConfig["subCaption"] = f"{increment} Increments"
    chartConfig["xAxisName"] = "Time"
    chartConfig["yAxisName"] = "Users"
    chartConfig["theme"] = "fusion"
    chartConfig["labelStep"] = "1"
    chartConfig["labelFontSize"] = "10"
    chartConfig["slantLabel"] = "1"

    dataSource["chart"] = chartConfig

    dataSource['data'] = []
    for timestamp in timeline:
        dataSource['data'].append(
            {
                "label": timestamp['_id'].strftime("%m/%d/%Y, %H:%M:%S") if \
                    timestamp['_id'].hour == 0 and timestamp['_id'].minute == 0 and\
                    timestamp['_id'].second == 0 else timestamp['_id'].strftime("%H:%M:%S"), 
                "value": timestamp['count']
            }
        )

    return FusionCharts("column2d", f"users-timeline-{datetime.now().strftime('%H/%M/%S')}", "1000", "400", "users-timeline-wrapper", "json", dataSource).render()


# Helper functions ===============================================================

def getTimestampArray(start, increment, additional):
    array = [{"_id": start, "count": "0"}]
    if increment == "daily":
        for next in range(1, additional+1):
            array.append({"_id": array[next-1]["_id"] + timedelta(days=1), "count": "0"})
    elif increment == "hourly":
        for next in range(1, additional+1):
            array.append({"_id": array[next-1]["_id"] + timedelta(hours=1), "count": "0"})
    elif increment == "5-minute":
        for next in range(1, additional+1):
            array.append({"_id": array[next-1]["_id"] + timedelta(minutes=5), "count": "0"})
    return array

def sortedZipLongest(l1, l2, key, fillvalue={}):  
    l1 = iter(sorted(l1, key=lambda x: x[key]))
    l2 = iter(sorted(l2, key=lambda x: x[key]))
    u = next(l1, None)
    v = next(l2, None)

    while (u is not None) or (v is not None):  
        if u is None:
            yield fillvalue, v
            v = next(l2, None)
        elif v is None:
            yield u, fillvalue
            u = next(l1, None)
        elif u.get(key) == v.get(key):
            yield u, v
            u = next(l1, None)
            v = next(l2, None)
        elif u.get(key) < v.get(key):
            yield u, fillvalue
            u = next(l1, None)
        else:
            yield fillvalue, v
            v = next(l2, None)