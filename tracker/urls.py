from django.urls import path
from .views import (
    live_location_logs,
    live_wristband_devices,
    location_logs_dashboard,
    receive_location_data,
    service_user_list,
)

app_name = "tracker"

urlpatterns = [
    path("users/", service_user_list, name="service_user_list"),

    path("location-logs/", location_logs_dashboard, name="location_logs_dashboard"),
    path("location-logs/live/", live_location_logs, name="live_location_logs"),

    path("wristbands/live/", live_wristband_devices, name="live_wristband_devices"),

    path("api/location/", receive_location_data, name="receive_location_data"),
]