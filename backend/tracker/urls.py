from django.urls import path
from .views import service_user_list   

app_name = "tracker"

urlpatterns = [
    path("users/", service_user_list, name="service_user_list"),
]