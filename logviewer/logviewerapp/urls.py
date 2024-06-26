from tkinter.font import names
from . import views
from django.urls import include, path
from rest_framework import routers
from django.views.generic.base import RedirectView
from datetime import datetime

router = routers.DefaultRouter()
router.register(r'logs', views.LogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth', include('rest_framework.urls', namespace='rest_framework')),

    path('', RedirectView.as_view(url='/log-viewer/listing/', permanent=True)),
    path('log-viewer/listing/', views.listing),
    path('log-viewer/listing/<str:id>', views.details),
    path('log-viewer/exceptions/', views.exceptionCategories),
    path('log-viewer/exceptions/timeline', views.timeline),
    path('log-viewer/exceptions/top-exceptions', views.topExceptions),
    path('log-viewer/users/', views.userInformation),
    path('log-viewer/users/session-duration', views.userDuration),
    path('log-viewer/users/users', views.users)
]