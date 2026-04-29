from django.contrib import admin
from django.urls import path
from tracker.views import receive_location_data

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/location/", receive_location_data, name="receive_location"),
]