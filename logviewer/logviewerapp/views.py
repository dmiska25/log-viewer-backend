from django.http import HttpResponse
from django.shortcuts import render
from . import urls

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. View here")
