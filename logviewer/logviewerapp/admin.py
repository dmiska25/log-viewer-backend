from django.contrib import admin

from .fields import MyJSONField
from .models import Log
from jsoneditor.forms import JSONEditor

# Register your models here.

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    formfield_overrides = {
        MyJSONField: {'widget': JSONEditor(attrs={'style': 'width: 620px;'}) }
    }