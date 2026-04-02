from django.urls import path
from .views import (
    add_task,
    live_location_logs,
    location_logs_dashboard,
    receive_location_data,
    service_user_list,
    task_alerts,
    task_dashboard,
    task_detail,
    update_task_status,
)

app_name = "tracker"

urlpatterns = [
    path("users/", service_user_list, name="service_user_list"),
    path("tasks/", task_dashboard, name="task_dashboard"),
    path("tasks/alerts/", task_alerts, name="task_alerts"),
    path("tasks/add/", add_task, name="add_task"),
    path("tasks/<int:task_id>/", task_detail, name="task_detail"),
    path("tasks/<int:task_id>/update/", update_task_status, name="update_task_status"),
    path("location-logs/", location_logs_dashboard, name="location_logs_dashboard"),
    path("location-logs/live/", live_location_logs, name="live_location_logs"),
    path("api/location/", receive_location_data, name="receive_location_data"),
]