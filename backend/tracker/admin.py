from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Resident, Wristband, DetectionEvent

admin.site.register(Resident)
admin.site.register(Wristband)
admin.site.register(DetectionEvent)