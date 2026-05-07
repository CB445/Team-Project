from django.urls import path

from .views import (
    home,
    add_task,
    live_location_logs,
    live_wristband_devices,
    latest_rfid_redirect,
    location_logs_dashboard,
    receive_location_data,
    service_user_list,
    task_alerts,
    task_dashboard,
    task_detail,
    update_task_status,
    service_user_profile_by_rfid,
)

app_name = "tracker"

urlpatterns = [
    path("", home, name="home"),

    path("users/", service_user_list, name="service_user_list"),

    path("tasks/", task_dashboard, name="task_dashboard"),
    path("tasks/alerts/", task_alerts, name="task_alerts"),
    path("tasks/add/", add_task, name="add_task"),
    path("tasks/<int:task_id>/", task_detail, name="task_detail"),
    path(
        "tasks/<int:task_id>/update/",
        update_task_status,
        name="update_task_status"
    ),

    path(
        "location-logs/",
        location_logs_dashboard,
        name="location_logs_dashboard"
    ),

    path(
        "location-logs/live/",
        live_location_logs,
        name="live_location_logs"
    ),

    path(
        "wristbands/live/",
        live_wristband_devices,
        name="live_wristband_devices"
    ),

    path(
        "api/location/",
        receive_location_data,
        name="receive_location_data"
    ),

    # IMPORTANT:
    # Put this BEFORE the dynamic RFID route
    path(
        "rfid/latest/",
        latest_rfid_redirect,
        name="latest_rfid_redirect"
    ),

    path(
        "rfid/<str:rfid_uid>/",
        service_user_profile_by_rfid,
        name="service_user_profile_by_rfid",
    ),
]