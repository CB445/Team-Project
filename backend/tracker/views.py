from django.shortcuts import render
from .models import ServiceUser

def service_user_list(request):
    service_users = ServiceUser.objects.all()
    context = {
        "service_users": service_users,
    }
    return render(request, "tracker/service_users.html", context)